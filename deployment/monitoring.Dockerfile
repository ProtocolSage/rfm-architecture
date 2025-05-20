FROM prom/prometheus:latest AS prometheus
FROM grafana/grafana:latest

USER root

# Install tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy Prometheus binaries from the Prometheus image
COPY --from=prometheus /bin/prometheus /bin/prometheus
COPY --from=prometheus /bin/promtool /bin/promtool
COPY --from=prometheus /etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
COPY --from=prometheus /usr/share/prometheus/console_libraries/ /usr/share/prometheus/console_libraries/
COPY --from=prometheus /usr/share/prometheus/consoles/ /usr/share/prometheus/consoles/

# Create Prometheus configuration
RUN mkdir -p /etc/prometheus/rules

# Copy our custom Prometheus config
COPY deployment/prometheus/ /etc/prometheus/

# Create directories for Prometheus and Grafana data
RUN mkdir -p /prometheus /var/lib/grafana
RUN chown -R grafana:grafana /var/lib/grafana

# Copy Grafana provisioning files
COPY deployment/grafana/provisioning/ /etc/grafana/provisioning/
COPY deployment/grafana/dashboards/ /var/lib/grafana/dashboards/

# Create startup script for running both Prometheus and Grafana
RUN echo '#!/bin/bash\n\
# Start Prometheus in the background\n\
/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles \
  --web.listen-address=:9090 &\n\
\n\
# Start Grafana\n\
/run.sh\n' > /start.sh \
&& chmod +x /start.sh

# Expose Grafana and Prometheus ports
EXPOSE 3000 9090

# Start both services
CMD ["/start.sh"]