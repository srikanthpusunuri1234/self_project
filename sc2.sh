#!/bin/bash

# Ensure we are in the root directory
# Run this from inside the mysql-sharding-lab folder
BASE_DIR="spring-app"
JAVA_PATH="$BASE_DIR/src/main/java/com/example/demo"

# Create directory structure
mkdir -p "$JAVA_PATH/controller"
mkdir -p "$JAVA_PATH/service"
mkdir -p "$JAVA_PATH/config"
mkdir -p "$JAVA_PATH/model"

# Create root level files for the app
touch "$BASE_DIR/pom.xml"
touch "application.yml"

# Create Java files
touch "$JAVA_PATH/DemoApplication.java"
touch "$JAVA_PATH/controller/UserController.java"
touch "$JAVA_PATH/service/UserService.java"
touch "$JAVA_PATH/config/DataSourceConfig.java"
touch "$JAVA_PATH/model/User.java"

echo "✅ Spring Boot structure created successfully!"
