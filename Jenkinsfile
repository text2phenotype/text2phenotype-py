
final dockerRepo = "docker.text2phenotype.com"
final image_name = "text2phenotype-py"
def full_hash
def short_hash
def build_timestamp_tag = env.BUILD_TIMESTAMP_TAG

// These variables come from the build parameters in the Jenkins job
def git_branch = git_branch
def git_repo = git_repo


pipeline  {
  agent {
    kubernetes {
      cloud 'eks-tools-prod-20191113'
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker.text2phenotype.com/docker:dind
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
      - name: jenkins-docker-cfg
        mountPath: /root/.docker
      - name: docker-graph-storage
        mountPath: /var/lib/docker
  volumes:
  - name: "docker-graph-storage"
    emptyDir: {}
  - name: jenkins-docker-cfg
    projected:
      sources:
      - secret:
          name: text2phenotype
          items:
            - key: .dockerconfigjson
              path: config.json
"""
    }
  }
  options { skipDefaultCheckout() }

  stages {
    stage('Clone git repository') {
      steps {
        script {
          def scmVars = checkout(
            changelog: false,
            poll: false,
            scm: [$class: 'GitSCM',
              branches: [[name: git_branch]],
              doGenerateSubmoduleConfigurations: false,
              extensions: [[$class: 'SubmoduleOption',
                disableSubmodules: false,
                parentCredentials: true,
                recursiveSubmodules: false,
                reference: '',
                trackingSubmodules: false]],
              submoduleCfg: [],
              userRemoteConfigs: [[credentialsId: '8fda06db-84a1-4494-b78c-7b0d52d5a9d4',
                url: git_repo]]
              ]
          )
          echo "scmVars.GIT_COMMIT"
          echo "${scmVars.GIT_COMMIT}"
          env.GIT_COMMIT = scmVars.GIT_COMMIT
          echo "env.GIT_COMMIT"
          echo "${env.GIT_COMMIT}"
          full_hash = scmVars.GIT_COMMIT
          echo "full_hash: ${full_hash}"
          short_hash = full_hash.substring(0,8)
          echo "short_hash: ${short_hash}"
          env.DOCKER_REPO = dockerRepo
          env.DOCKER_GIT_REPO = git_repo
          env.DOCKER_TAG = git_branch + "_" + short_hash + "_" + build_timestamp_tag
          env.IMAGE_NAME = image_name
          env.WORKSPACE_HOME = "${env.JENKINS_AGENT_WORKDIR}/workspace/${env.JOB_BASE_NAME}"

        }
        sh 'env'
        withCredentials([string(credentialsId: 'GOOGLE_APPLICATION_CREDENTIALS_JSON', variable: 'GOOGLE_APPLICATION_CREDS')]) {
            script {
                env.GOOGLEAPI = env.GOOGLE_APPLICATION_CREDS
            }
        }
      }
    }
    stage('run suite-runner script') {
      steps {
        container(name: 'docker', shell: '/bin/bash') {
          sh """#!/bin/bash
            export DOCKER_TARGET_ORG=${env.DOCKER_REPO}
            export GOOGLE_APPLICATION_CREDENTIALS_JSON=${env.GOOGLEAPI}
            env
            cd ${env.JENKINS_AGENT_WORKDIR}/workspace/${env.JOB_BASE_NAME}
            source ./build-tools/bin/suite-runner -D
          """
        }
      }
    }
  }
  post {
    success {
      addGitLabMRComment comment: 'Pipeline ran successfully'
      updateGitlabCommitStatus name: 'Pipeline ran successfully', state: 'success'
    }
    aborted {
      addGitLabMRComment comment: 'Pipeline has been aborted'
      updateGitlabCommitStatus name: 'Pipeline has been aborted', state: 'canceled'
    }
    failure {
      addGitLabMRComment comment: 'Pipeline has failed'
      updateGitlabCommitStatus name: 'Pipeline has been failed', state: 'failed'
    }
  }
}
