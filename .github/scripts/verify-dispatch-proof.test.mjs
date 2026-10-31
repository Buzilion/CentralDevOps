import assert from 'node:assert/strict';
import { createHash, generateKeyPairSync, randomBytes, sign } from 'node:crypto';
import test from 'node:test';
import { VerificationFailure, verifyDispatchProof } from './verify-dispatch-proof.mjs';

const { privateKey, publicKey } = generateKeyPairSync('rsa', {
  modulusLength: 2048,
  publicExponent: 0x10001,
});
const testKeyId = 'generated-test-key';
const testJwks = {
  keys: [
    {
      ...publicKey.export({ format: 'jwk' }),
      kid: testKeyId,
      use: 'sig',
      alg: 'RS256',
    },
  ],
};
const nowSeconds = 1_800_000_000;

function audienceForTest(environment, imageRef, bundleBytes) {
  const bytes = Buffer.concat([
    Buffer.from(environment, 'utf8'),
    Buffer.from([0x7c]),
    Buffer.from(imageRef, 'utf8'),
    Buffer.from([0x7c]),
    bundleBytes,
  ]);
  return `centraldevops-deploy:${createHash('sha256').update(bytes).digest('hex')}`;
}

function encodeJson(value) {
  return Buffer.from(JSON.stringify(value), 'utf8').toString('base64url');
}

function signClaims(claims) {
  const header = encodeJson({ typ: 'JWT', alg: 'RS256', kid: testKeyId });
  const payload = encodeJson(claims);
  const signingInput = `${header}.${payload}`;
  const signature = sign('RSA-SHA256', Buffer.from(signingInput, 'ascii'), privateKey)
    .toString('base64url');
  return `${signingInput}.${signature}`;
}

function makeProof(options = {}) {
  const targetEnvironment = options.targetEnvironment ?? 'Staging';
  const imageRef =
    options.imageRef ?? 'ghcr.io/buzilion/dispatch-proof@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
  const bundleBytes = options.bundleBytes ?? randomBytes(32);
  const sealedBundleBase64 =
    options.sealedBundleBase64 ?? bundleBytes.toString('base64');
  const claims = {
    iss: 'https://token.actions.githubusercontent.com',
    aud: audienceForTest(targetEnvironment, imageRef, bundleBytes),
    exp: nowSeconds + 300,
    repository: 'Buzilion/TestRepo-Application',
    job_workflow_ref:
      'Buzilion/TestRepo-Application/.github/workflows/deploy.yml@refs/heads/main',
    ref: 'refs/heads/main',
    environment: targetEnvironment,
    run_id: '1234567890',
    run_attempt: '1',
    ...options.claimOverrides,
  };

  return {
    targetEnvironment,
    imageRef,
    oidcToken: signClaims(claims),
    sealedBundleBase64,
    centralRef: options.centralRef ?? 'refs/heads/feature/02_dispatch-trust-proof',
    dispatchActor: options.dispatchActor ?? 'buzilion-dispatch-proof[bot]',
  };
}

async function verify(inputs) {
  return verifyDispatchProof(inputs, { jwks: testJwks, nowSeconds });
}

function rejectsWithCheck(promise, check) {
  return assert.rejects(
    promise,
    (error) => error instanceof VerificationFailure && error.check === check,
  );
}

test('accepts a signed Staging proof from a non-main CentralDevOps branch', async () => {
  const outputs = await verify(makeProof());

  assert.deepEqual(outputs, {
    environment: 'Staging',
    repository: 'Buzilion/TestRepo-Application',
    job_workflow_ref:
      'Buzilion/TestRepo-Application/.github/workflows/deploy.yml@refs/heads/main',
    ref: 'refs/heads/main',
    run_id: '1234567890',
    run_attempt: '1',
    check_central_ref: 'passed',
    check_bundle_encoding: 'passed',
    check_oidc_signature: 'passed',
    check_issuer: 'passed',
    check_expiry: 'passed',
    check_audience_binding: 'passed',
    check_required_claims: 'passed',
    check_source_fixture: 'passed',
    check_source_claims: 'passed',
    check_dispatch_actor: 'passed',
  });
});

test('accepts Production only from release branches', async () => {
  const outputs = await verify(
    makeProof({
      targetEnvironment: 'Production',
      centralRef: 'refs/heads/release/proof-candidate',
    }),
  );
  assert.equal(outputs.environment, 'Production');

  await rejectsWithCheck(
    verify(
      makeProof({
        targetEnvironment: 'Production',
        centralRef: 'refs/heads/main',
      }),
    ),
    'central_ref',
  );
});

test('rejects non-canonical base64 that Buffer.from would otherwise accept', async () => {
  const proof = makeProof();
  proof.sealedBundleBase64 = `${proof.sealedBundleBase64}\n`;
  await rejectsWithCheck(verify(proof), 'bundle_encoding');
});

test('rejects a payload changed after the audience was issued', async () => {
  const proof = makeProof();
  proof.imageRef = `${proof.imageRef}-changed`;
  await rejectsWithCheck(verify(proof), 'audience_binding');
});

test('rejects a bundle changed after the audience was issued', async () => {
  const proof = makeProof();
  proof.sealedBundleBase64 = randomBytes(32).toString('base64');
  await rejectsWithCheck(verify(proof), 'audience_binding');
});

test('binds runtime-generated bundle bytes without text normalization', async () => {
  const outputs = await verify(makeProof({ bundleBytes: randomBytes(32) }));
  assert.equal(outputs.check_audience_binding, 'passed');
});

test('rejects an invalid JWT signature', async () => {
  const proof = makeProof();
  const segments = proof.oidcToken.split('.');
  const firstCharacter = segments[2][0] === 'A' ? 'B' : 'A';
  segments[2] = `${firstCharacter}${segments[2].slice(1)}`;
  proof.oidcToken = segments.join('.');
  await rejectsWithCheck(verify(proof), 'oidc_signature');
});

test('rejects an invalid issuer and malformed or mismatched audience', async () => {
  await rejectsWithCheck(
    verify(makeProof({ claimOverrides: { iss: 'https://issuer.invalid' } })),
    'issuer',
  );
  await rejectsWithCheck(
    verify(
      makeProof({
        claimOverrides: { aud: 'centraldevops-deploy:not-a-sha256-digest' },
      }),
    ),
    'audience_binding',
  );
  await rejectsWithCheck(
    verify(makeProof({ claimOverrides: { aud: ['centraldevops-deploy:wrong'] } })),
    'audience_binding',
  );
});

test('rejects an unexpected dispatch actor independently of the signed proof', async () => {
  const proof = makeProof({ dispatchActor: 'unexpected-user' });
  await rejectsWithCheck(verify(proof), 'dispatch_actor');
});

test('rejects expired tokens and missing required evidence claims', async () => {
  await rejectsWithCheck(
    verify(makeProof({ claimOverrides: { exp: nowSeconds - 1 } })),
    'expiry',
  );
  for (const claim of [
    'repository',
    'job_workflow_ref',
    'ref',
    'environment',
    'run_id',
    'run_attempt',
  ]) {
    await rejectsWithCheck(
      verify(makeProof({ claimOverrides: { [claim]: undefined } })),
      'required_claims',
    );
  }
});

test('rejects mismatched source repository, workflow, ref, or Environment claims', async () => {
  const cases = [
    [{ repository: 'Buzilion/Unregistered' }, 'source_repository'],
    [
      {
        job_workflow_ref:
          'Buzilion/TestRepo-Application/.github/workflows/other.yml@refs/heads/main',
      },
      'source_workflow',
    ],
    [{ ref: 'refs/heads/feature/other' }, 'source_ref'],
    [{ environment: 'Production' }, 'source_environment'],
  ];

  for (const [claimOverrides, check] of cases) {
    await rejectsWithCheck(
      verify(makeProof({ claimOverrides })),
      check,
    );
  }
});
