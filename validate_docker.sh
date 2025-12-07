#!/bin/bash

echo "🔍 Validating Docker configuration..."
echo ""

# Check if Dockerfile exists
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile exists"
else
    echo "❌ Dockerfile not found"
    exit 1
fi

# Check if docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml exists"
else
    echo "❌ docker-compose.yml not found"
    exit 1
fi

# Validate Dockerfile syntax
echo ""
echo "�� Dockerfile content validation:"
echo "   - Base image: $(grep -m1 'FROM' Dockerfile | cut -d' ' -f2)"
echo "   - Working directory: $(grep -m1 'WORKDIR' Dockerfile | cut -d' ' -f2)"
echo "   - Exposed ports: $(grep 'EXPOSE' Dockerfile | cut -d' ' -f2-)"
echo "   - Entry point: $(grep -m1 'CMD' Dockerfile | cut -d'[' -f2 | cut -d']' -f1)"

# Check for required files
echo ""
echo "📦 Checking required files:"
files=("requirements.txt" "pyproject.toml" "src/estimatex/web.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file not found"
    fi
done

# Check docker-compose services
echo ""
echo "🐳 Docker Compose services:"
grep -A1 "^  [a-z]" docker-compose.yml | grep -v "^--$" | grep ":" | head -8

echo ""
echo "✨ Docker configuration validation complete!"
echo ""
echo "📌 To build the Docker image (requires Docker running):"
echo "   docker build -t estimatex:latest ."
echo ""
echo "📌 To start all services:"
echo "   docker-compose up -d"
echo ""
echo "📌 To start only the web service:"
echo "   docker-compose up -d web"
