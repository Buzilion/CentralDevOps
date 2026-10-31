import { createHash, createPublicKey, verify as verifySignature } from 'node:crypto';
import { appendFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { TextDecoder } from 'node:util';

const JWKS_URL = 'https://token.actions.githubusercontent.com/.well-known/jwks';
const EXPECTED_ISSUER = 'https://token.actions.githubusercontent.com';
const EXPECTED_DISPATCH_ACTOR = 'buzilion-dispatch-proof[bot]';
const MAX_JWT_LENGTH = 32_768;
const MAX_BUNDLE_BASE64_LENGTH = 65_535;
const MAX_JWKS_BYTES = 1_048_576;
const STANDARD_BASE64 = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
const BASE64URL = /^[A-Za-z0-9_-]+$/;
const REQUIRED_EVIDENCE_CLAIMS = [
  'repository',
  'job_workflow_ref',
  'ref',
  'environment',
  'run_id',
  'run_attempt',
];

const SOURCE_FIXTURES = Object.freeze({
  'Buzilion/TestRepo-Application': Object.freeze({
    appIdentity: 'buzilion-dispatch-proof[bot]',
    jobWorkflowRef:
      'Buzilion/TestRepo-Application/.github/workflows/deploy.yml@refs/heads/main',
    ref: 'refs/heads/main',
  }),
});

export class VerificationFailure extends Error {
  constructor(check) {
    super(check);
    this.name = 'VerificationFailure';
    this.check = check;
  }
}

function fail(check) {
  throw new VerificationFailure(check);
}

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, check) {
  if (typeof value !== 'string' || value.length === 0) {
    fail(check);
  }
  return value;
}

export function validateCentralRef(targetEnvironment, centralRef) {
  const ref = requireString(centralRef, 'central_ref');
  const branchPrefix = 'refs/heads/';

  if (targetEnvironment === 'Staging') {
    if (!ref.startsWith(branchPrefix) || ref.length === branchPrefix.length) {
      fail('central_ref');
    }
    return;
  }

  if (targetEnvironment === 'Production') {
    const releasePrefix = 'refs/heads/release/';
    if (!ref.startsWith(releasePrefix) || ref.length === releasePrefix.length) {
      fail('central_ref');
    }
    return;
  }

  fail('target_environment');
}

export function decodeCanonicalBase64(value) {
  if (
    typeof value !== 'string' ||
    value.length === 0 ||
    value.length > MAX_BUNDLE_BASE64_LENGTH ||
    value.length % 4 !== 0 ||
    !STANDARD_BASE64.test(value)
  ) {
    fail('bundle_encoding');
  }

  const bytes = Buffer.from(value, 'base64');
  if (bytes.length === 0 || bytes.toString('base64') !== value) {
    fail('bundle_encoding');
  }
  return bytes;
}

export function computeAudience(targetEnvironment, imageRef, bundleBytes) {
  const environmentBytes = Buffer.from(requireString(targetEnvironment, 'dispatch_input'), 'utf8');
  const imageRefBytes = Buffer.from(requireString(imageRef, 'dispatch_input'), 'utf8');
  if (!Buffer.isBuffer(bundleBytes)) {
    fail('dispatch_input');
  }

  const digest = createHash('sha256')
    .update(environmentBytes)
    .update(Buffer.from([0x7c]))
    .update(imageRefBytes)
    .update(Buffer.from([0x7c]))
    .update(bundleBytes)
    .digest('hex');

  return `centraldevops-deploy:${digest}`;
}

function decodeBase64UrlSegment(segment, check) {
  if (
    typeof segment !== 'string' ||
    segment.length === 0 ||
    segment.length % 4 === 1 ||
    !BASE64URL.test(segment)
  ) {
    fail(check);
  }

  const bytes = Buffer.from(segment, 'base64url');
  if (bytes.toString('base64url') !== segment) {
    fail(check);
  }
  return bytes;
}

function parseJsonObject(bytes, check) {
  let value;
  try {
    value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch {
    fail(check);
  }
  if (!isRecord(value)) {
    fail(check);
  }
  return value;
}

function parseCompactJwt(token) {
  if (typeof token !== 'string' || token.length === 0 || token.length > MAX_JWT_LENGTH) {
    fail('jwt_format');
  }

  const segments = token.split('.');
  if (segments.length !== 3) {
    fail('jwt_format');
  }

  const header = parseJsonObject(
    decodeBase64UrlSegment(segments[0], 'jwt_header'),
    'jwt_header',
  );
  const payloadBytes = decodeBase64UrlSegment(segments[1], 'jwt_format');
  const signature = decodeBase64UrlSegment(segments[2], 'jwt_format');

  if (
    header.alg !== 'RS256' ||
    typeof header.kid !== 'string' ||
    header.kid.length === 0 ||
    (header.typ !== undefined && header.typ !== 'JWT') ||
    header.crit !== undefined ||
    header.b64 !== undefined
  ) {
    fail('jwt_header');
  }

  return {
    header,
    headerSegment: segments[0],
    payloadSegment: segments[1],
    payloadBytes,
    signature,
  };
}

export async function fetchPublishedJwks(fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== 'function') {
    fail('jwks_fetch');
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);

  try {
    const response = await fetchImpl(JWKS_URL, {
      method: 'GET',
      headers: { accept: 'application/json' },
      redirect: 'error',
      signal: controller.signal,
    });
    if (!response || !response.ok) {
      fail('jwks_fetch');
    }

    const contentLength = response.headers?.get('content-length');
    if (contentLength !== null && contentLength !== undefined) {
      const parsedLength = Number(contentLength);
      if (Number.isFinite(parsedLength) && parsedLength > MAX_JWKS_BYTES) {
        fail('jwks_format');
      }
    }

    const text = await response.text();
    if (Buffer.byteLength(text, 'utf8') > MAX_JWKS_BYTES) {
      fail('jwks_format');
    }

    let jwks;
    try {
      jwks = JSON.parse(text);
    } catch {
      fail('jwks_format');
    }
    if (!isRecord(jwks) || !Array.isArray(jwks.keys)) {
      fail('jwks_format');
    }
    return jwks;
  } catch (error) {
    if (error instanceof VerificationFailure) {
      throw error;
    }
    fail('jwks_fetch');
  } finally {
    clearTimeout(timeout);
  }
}

function findSigningKey(jwks, keyId) {
  if (!isRecord(jwks) || !Array.isArray(jwks.keys)) {
    fail('jwks_format');
  }

  const matchingKeys = jwks.keys.filter(
    (key) => isRecord(key) && key.kid === keyId,
  );
  if (matchingKeys.length !== 1) {
    fail('jwks_key');
  }

  const jwk = matchingKeys[0];
  if (
    jwk.kty !== 'RSA' ||
    typeof jwk.n !== 'string' ||
    typeof jwk.e !== 'string' ||
    jwk.d !== undefined ||
    (jwk.use !== undefined && jwk.use !== 'sig') ||
    (jwk.alg !== undefined && jwk.alg !== 'RS256') ||
    (jwk.key_ops !== undefined &&
      (!Array.isArray(jwk.key_ops) || !jwk.key_ops.includes('verify')))
  ) {
    fail('jwks_key');
  }

  let publicKey;
  try {
    publicKey = createPublicKey({
      key: { kty: 'RSA', n: jwk.n, e: jwk.e },
      format: 'jwk',
    });
  } catch {
    fail('jwks_key');
  }

  const details = publicKey.asymmetricKeyDetails;
  if (
    publicKey.asymmetricKeyType !== 'rsa' ||
    !details ||
    details.modulusLength < 2048
  ) {
    fail('jwks_key');
  }
  return publicKey;
}

function verifyJwtSignature(parsedToken, jwks) {
  const publicKey = findSigningKey(jwks, parsedToken.header.kid);
  const signingInput = Buffer.from(
    `${parsedToken.headerSegment}.${parsedToken.payloadSegment}`,
    'ascii',
  );

  let valid;
  try {
    valid = verifySignature('RSA-SHA256', signingInput, publicKey, parsedToken.signature);
  } catch {
    fail('oidc_signature');
  }
  if (!valid) {
    fail('oidc_signature');
  }
}

function validateClaims(claims, inputs, expectedAudience, nowSeconds) {
  if (claims.iss !== EXPECTED_ISSUER) {
    fail('issuer');
  }
  if (!Number.isSafeInteger(claims.exp) || claims.exp <= nowSeconds) {
    fail('expiry');
  }
  if (
    claims.nbf !== undefined &&
    (!Number.isSafeInteger(claims.nbf) || claims.nbf > nowSeconds)
  ) {
    fail('not_before');
  }

  for (const name of REQUIRED_EVIDENCE_CLAIMS) {
    if (typeof claims[name] !== 'string' || claims[name].length === 0) {
      fail('required_claims');
    }
  }
  if (
    !/^[1-9][0-9]*$/.test(claims.run_id) ||
    !/^[1-9][0-9]*$/.test(claims.run_attempt)
  ) {
    fail('required_claims');
  }

  if (claims.aud !== expectedAudience) {
    fail('audience_binding');
  }

  if (!Object.prototype.hasOwnProperty.call(SOURCE_FIXTURES, claims.repository)) {
    fail('source_repository');
  }
  const sourceFixture = SOURCE_FIXTURES[claims.repository];
  if (sourceFixture.appIdentity !== EXPECTED_DISPATCH_ACTOR) {
    fail('source_fixture');
  }
  if (claims.job_workflow_ref !== sourceFixture.jobWorkflowRef) {
    fail('source_workflow');
  }
  if (claims.ref !== sourceFixture.ref) {
    fail('source_ref');
  }
  if (claims.environment !== inputs.targetEnvironment) {
    fail('source_environment');
  }
  if (
    inputs.dispatchActor !== EXPECTED_DISPATCH_ACTOR ||
    inputs.dispatchActor !== sourceFixture.appIdentity
  ) {
    fail('dispatch_actor');
  }
}

export async function verifyDispatchProof(inputs, options = {}) {
  if (!isRecord(inputs) || !isRecord(options)) {
    fail('dispatch_input');
  }

  const targetEnvironment = requireString(inputs.targetEnvironment, 'dispatch_input');
  if (targetEnvironment !== 'Staging' && targetEnvironment !== 'Production') {
    fail('target_environment');
  }
  if (inputs.dispatchActor !== EXPECTED_DISPATCH_ACTOR) {
    fail('dispatch_actor');
  }

  const imageRef = requireString(inputs.imageRef, 'dispatch_input');
  validateCentralRef(targetEnvironment, inputs.centralRef);

  const bundleBytes = decodeCanonicalBase64(inputs.sealedBundleBase64);
  const expectedAudience = computeAudience(targetEnvironment, imageRef, bundleBytes);

  const parsedToken = parseCompactJwt(inputs.oidcToken);
  const nowSeconds =
    options.nowSeconds === undefined ? Math.floor(Date.now() / 1000) : options.nowSeconds;
  if (!Number.isSafeInteger(nowSeconds)) {
    fail('verifier_clock');
  }

  let jwks = options.jwks;
  if (jwks === undefined) {
    const loadJwks = options.fetchJwks ?? fetchPublishedJwks;
    if (typeof loadJwks !== 'function') {
      fail('jwks_fetch');
    }
    jwks = await loadJwks();
  }

  verifyJwtSignature(parsedToken, jwks);
  const claims = parseJsonObject(parsedToken.payloadBytes, 'oidc_claims');
  validateClaims(claims, { targetEnvironment, dispatchActor: inputs.dispatchActor }, expectedAudience, nowSeconds);

  return {
    environment: claims.environment,
    repository: claims.repository,
    job_workflow_ref: claims.job_workflow_ref,
    ref: claims.ref,
    run_id: claims.run_id,
    run_attempt: claims.run_attempt,
    audience_expected: expectedAudience,
    audience_observed: claims.aud,
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
  };
}

function writeGitHubOutputs(outputs) {
  const outputPath = requireString(process.env.GITHUB_OUTPUT, 'output_write');
  const entries = Object.entries(outputs);
  for (const [name, value] of entries) {
    if (
      !/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) ||
      typeof value !== 'string' ||
      /[\r\n]/.test(value)
    ) {
      fail('output_safety');
    }
  }

  try {
    appendFileSync(
      outputPath,
      `${entries.map(([name, value]) => `${name}=${value}`).join('\n')}\n`,
      { encoding: 'utf8' },
    );
  } catch {
    fail('output_write');
  }
}

async function runCli() {
  try {
    const outputs = await verifyDispatchProof({
      targetEnvironment: process.env.TARGET_ENVIRONMENT,
      imageRef: process.env.IMAGE_REF,
      oidcToken: process.env.OIDC_TOKEN,
      sealedBundleBase64: process.env.SEALED_BUNDLE,
      centralRef: process.env.CENTRAL_REF,
      dispatchActor: process.env.DISPATCH_ACTOR,
    });
    writeGitHubOutputs(outputs);
  } catch (error) {
    const check = error instanceof VerificationFailure ? error.check : 'internal_verifier';
    process.stderr.write(`dispatch-proof verification failed: ${check}\n`);
    process.exitCode = 1;
  }
}

const scriptPath = fileURLToPath(import.meta.url);
if (process.argv[1] && resolve(process.argv[1]) === scriptPath) {
  void runCli();
}
