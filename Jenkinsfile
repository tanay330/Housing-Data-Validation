pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'housing-data-validation'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Pulling latest code from GitHub...'
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo 'Building Docker images...'
                sh 'docker compose build'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying all services...'
                sh 'docker compose down'
                sh 'docker compose up -d'
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking services are healthy...'
                sleep(time: 20, unit: 'SECONDS')
                sh 'curl -f http://localhost/health'
                sh 'curl -f http://localhost/auth/health'
                sh 'curl -f http://localhost/validate/health'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully! All services are running.'
        }
        failure {
            echo 'Pipeline failed! Check the logs above.'
            sh 'docker compose logs --tail=50'
        }
    }
}