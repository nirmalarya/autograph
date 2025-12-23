FROM nginx:1.25-alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create log directory
RUN mkdir -p /var/log/nginx

# Expose port
EXPOSE 8090

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
