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
                bat 'docker-compose build'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying all services...'
                bat 'docker-compose down'
                bat 'docker-compose up -d'
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking services are healthy...'
                sleep(time: 20, unit: 'SECONDS')
                bat 'curl -f http://localhost/health'
                bat 'curl -f http://localhost/auth/health'
                bat 'curl -f http://localhost/validate/health'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully! All services are running.'
        }
        failure {
            echo 'Pipeline failed! Check the logs above.'
            bat 'docker-compose logs'
        }
    }
}