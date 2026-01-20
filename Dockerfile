FROM homeassistant/home-assistant:latest

# Copy the custom component into the container
# This will be overridden by the volume mount in docker-compose
COPY custom_components/glkvm /config/custom_components/glkvm

# Expose the default Home Assistant port
EXPOSE 8123

# The base image already has the correct entrypoint
