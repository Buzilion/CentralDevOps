# Requirements Document

# Questions and Answers

1. What things do you need the most that could help your technical infrastructure in the long run?

For now, I only has 2 application that used by the internal teams. It doesn't need that much VPS nor computing power. But in the future, when I already has the storefront application, where there would be such a high-traffic I need to support the continious scaling and the surge scaling (like when on promotional days).

So, I need a way to reliably and quickly setup a VPS and deploy the application in there in minutes. I'm thinking of using GitHub Action for the CI/CD trigger interface and then Ansible for the VPS management automation.

Let's say in the future, I need to quickly setup 5 new VPS to support incoming traffic (with assumption I already has the VPS, because I need to research manually which provider is good and cheap). I will need a workflow to quickly setup those 5 VPS at the same time, enhanced the secuirity, configure networks, installing dependencies, and eventually deploy the app and running it.

2. How is the high-level view of the process?

Let's say I have 5 VPS ready. I will need to register each of the VPS onto Ansible inventory based on required environment (dev, staging, prod). After that, I will need a github action workflow that I trigger manually that will configure those VPS using available ansible playbook (that consist of roles, each role with it's different tasks). But, since the inventory lists all of the VPS, the system need to know which VPS is already configured and skip it (if possible, if not there need to be validation step in each role tasks).

The available playbooks will be chosen based on what the VPS will be used, whether it's an web server, application server, or database server (right now I think these 3 is sufficient enough), so each playbook will have a similar roles and tasks, but will have distinct configuration.

3. What happens after the VPS is configured and ready to use?

Then, the next step would be to trigger each application repository GitHub action workflow. Each application will have decided to use which suitable VPS for them.

It will first run the CI process like formatting, linting, testing (unit/integration/build), and security scan. Then, after all are passed, it will continue to the CD process. The user will have manual deployment trigger accross the DEV, STAGING, and PROD environment, and will proceed sequentially (meaning user can't deploy to PROD directly without generated artifact on the DEV deployment phase).

On DEV deployment, the application will be built, and the artifact will be uploaded to Docker image. Then, it will use Ansible to communicate with the VPS to download the Docker image and actually run the application on the VPS.

The STAGING and PROD deployment will use the DEV build artifact on the docker image as the SoT. It will also use Ansible to communicate with the STAGING/PROD VPS to download and run the app via docker.

