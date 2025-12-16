FROM node:18.16.0

WORKDIR /app 

# Copy package files first for better caching
COPY src/frontend/package.json ./

# Install dependencies with npm (more reliable than yarn without lock file)
# Use --legacy-peer-deps to bypass React version conflicts
RUN npm install --legacy-peer-deps

# Fix ajv module resolution issues
RUN npm install ajv@^8.12.0 ajv-keywords@^5.1.0 --legacy-peer-deps

# Verify react-scripts is installed
RUN ls -la node_modules/.bin/react-scripts || echo "react-scripts not found in .bin"
RUN ls -la node_modules/react-scripts/ || echo "react-scripts package not found"

# Copy the rest of the app
COPY src/frontend .

# Create the digital_data directory structure
RUN mkdir -p /app/public/digital_data/personal-data

# Copy sample data for demo purposes (optional)
COPY sample_data /app/public/digital_data/sample_data

# Create symlinks for actual data (will be available when volumes are mounted)
# The MyData directory will be mounted from the host via docker-compose volumes
RUN ln -sf /app/MyData /app/public/digital_data/MyData && \
    ln -sf /app/MyData/app_data /app/public/digital_data/personal-data/app_data

CMD ["npm", "start"]