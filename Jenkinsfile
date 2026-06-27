pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/tanay330/housing-data-validation.git'
            }
        }
        stage('Build') {
            steps {
                sh 'docker compose build'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker compose down'
                sh 'docker compose up -d'
            }
        }
        stage('Health Check') {
            steps {
                sleep(time: 20, unit: 'SECONDS')
                sh 'docker exec nginx_proxy curl -f http://localhost/health'
            }
        }
    }
    post {
        success {
            echo 'SUCCESS'
        }
        failure {
            echo 'FAILED'
        }
    }
}