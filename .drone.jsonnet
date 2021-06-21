/* Docker images */
local images = {
  drone_gke: 'nytimes/drone-gke:0.10.0@sha256:03b3dbfade3367c25999ec1d52d0b0fe11ce91d66777b1868951ee4260f25824',
  gcr: 'plugins/gcr:18@sha256:5868a924a88b667f9d4a3fd22a8381d8e6927786e3a50e49fb43c83256430fdf',
  node: 'node:14.17.0@sha256:c441936a8aad0da25eb24dfbb53ec6d159595186762d636db356f62f2991d71b',
};

/* Secrets used for deployment of dev, prd */
local secrets = {
  google: {
    // vault read vault read nytimes/teams/news-maintainers/secret/monorepo/service-account-keys/google/nyt-news-dev/drone-ci
    drone_ci_dev: {
      from_secret: 'gcp_nyt_news_dev_drone_ci',
    },
    // vault read vault read nytimes/teams/news-maintainers/secret/monorepo/service-account-keys/google/nyt-news-prd/drone-ci
    drone_ci_prd: {
      from_secret: 'gcp_nyt_news_prd_drone_ci',
    },
  },
  ci_butler: {
    // vault read nytm/wf-user-secrets/secret/monorepo/drone-ci-butler-dev
    dev: {
      app_id: {
        from_secret: 'ci_butler_app_id_dev',
      },
      private_key: {
        from_secret: 'ci_butler_private_key_dev',
      },
      webhook: {
        from_secret: 'ci_butler_webhook_secret_dev',
      },
    },
    // vault read nytm/wf-user-secrets/secret/monorepo/drone-ci-butler-prd
    prd: {
      app_id: {
        from_secret: 'ci_butler_app_id_prd',
      },
      private_key: {
        from_secret: 'ci_butler_private_key_prd',
      },
      webhook: {
        from_secret: 'ci_butler_webhook_secret_prd',
      },
    },
  },
};

/* Base configuration for most pipeline steps */
local base = { pull: 'if-not-exists' };
local base_node = base { image: images.node };

/* Main pipeline */
[{
  kind: 'pipeline',
  type: 'docker',
  name: 'ci_butler',
  steps: [
    base_node {
      name: 'yarn',
      commands: ['yarn'],
      when: { event: 'push' },
    },
    base_node {
      name: 'yarn lint',
      depends_on: ['yarn'],
      commands: ['yarn lint'],
      when: { event: 'push' },
    },
    base_node {
      name: 'yarn test',
      depends_on: ['yarn'],
      commands: ['yarn test'],
      when: { event: 'push' },
    },
    base_node {
      name: 'yarn build',
      depends_on: ['yarn'],
      commands: [
        'yarn build',
      ],
      environment: {
        NODE_ENV: 'production',
      },
      when: { event: 'push' },
    },
    base {
      image: images.gcr,
      name: 'gcr-dev',
      depends_on: ['yarn test', 'yarn lint', 'yarn build'],
      settings: {
        registry: 'us-docker.pkg.dev',
        repo: 'nyt-news-dev/github/drone-ci-butler',
        tag: [
          '${DRONE_COMMIT}',
          'latest',
        ],
        json_key: secrets.google.drone_ci_dev,
      },
      when: { event: 'push', branch: { exclude: ['main'] } },
    },
    base {
      image: images.drone_gke,
      name: 'deploy-dev',
      depends_on: ['gcr-dev'],
      settings: {
        cluster: 'engaged-turkey',
        namespace: 'github',
        project: 'nyt-news-dev',
        region: 'us-east1',
        token: secrets.google.drone_ci_dev,
        vars: {
          DNS_NAME: 'drone-ci-butler.news.dev.nyt.net',
          IMAGE: 'us-docker.pkg.dev/nyt-news-dev/github/drone-ci-butler:${DRONE_COMMIT}',
          LOG_LEVEL: 'info',
          NODE_ENV: 'production',
        },
        verbose: true,
        wait_deployments: [
          'ci_butler',
        ],
        wait_seconds: 600,
      },
      environment: {
        SECRET_CI_BUTLER_APP_ID: secrets.ci_butler.dev.app_id,
        SECRET_CI_BUTLER_PRIVATE_KEY: secrets.ci_butler.dev.private_key,
        SECRET_CI_BUTLER_WEBHOOK_SECRET: secrets.ci_butler.dev.webhook,
      },
      when: { event: 'push', branch: { exclude: [
        'dependabot-*',
        'dependabot/*',
        'main',
      ] } },
    },
    // TODO Convert to use the GCR tag/promotion thing like we do in
    // nytm/wf-project-vi for copying a dev Docker image to prd.
    base {
      image: images.gcr,
      name: 'gcr-prd',
      depends_on: ['yarn test', 'yarn lint', 'yarn build'],
      settings: {
        registry: 'us-docker.pkg.dev',
        repo: 'nyt-news-prd/github/drone-ci-butler',
        tag: [
          '${DRONE_COMMIT}',
          'latest',
        ],
        json_key: secrets.google.drone_ci_prd,
      },
      when: { event: ['push'], branch: ['main'] },
    },
    base {
      image: images.drone_gke,
      name: 'deploy-prd',
      depends_on: ['gcr-prd'],
      settings: {
        cluster: 'decent-leech',
        namespace: 'github',
        project: 'nyt-news-prd',
        region: 'us-east1',
        token: secrets.google.drone_ci_prd,
        vars: {
          DNS_NAME: 'drone-ci-butler.news.nyt.net',
          IMAGE: 'us-docker.pkg.dev/nyt-news-prd/github/drone-ci-butler:${DRONE_COMMIT}',
          LOG_LEVEL: 'info',
          NODE_ENV: 'production',
        },
        verbose: true,
        wait_deployments: [
          'ci_butler',
        ],
        wait_seconds: 600,
      },
      environment: {
        SECRET_CI_BUTLER_APP_ID: secrets.ci_butler.prd.app_id,
        SECRET_CI_BUTLER_PRIVATE_KEY: secrets.ci_butler.prd.private_key,
        SECRET_CI_BUTLER_WEBHOOK_SECRET: secrets.ci_butler.prd.webhook,
      },
      when: { event: ['push'], branch: ['main'] },
    },
  ],
}]
