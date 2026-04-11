# Production Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Production Environment Setup](#production-environment-setup)
3. [LLM Provider Configuration](#llm-provider-configuration)
4. [Security Configuration](#security-configuration)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Performance Optimization](#performance-optimization)
7. [Scaling Considerations](#scaling-considerations)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
9. [Troubleshooting](#troubleshooting)
10. [Deployment Checklist](#deployment-checklist)

## Overview

This guide covers deploying the AI PowerPoint Presentation Generator in a production environment. The system is designed as a CLI tool but can be integrated into larger workflows or services.

### Production Architecture

```
┌─────────────────┐
│   Application   │
│   Server(s)     │
└────────┬────────┘
         │
         ├─────────► IBM watsonx.ai (Primary LLM)
         │
         ├─────────► Anthropic Claude (Fallback LLM)
         │
         └─────────► File Storage (Templates, Outputs)
```

## Production Environment Setup

### System Requirements

**Minimum Requirements**:

- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB (+ storage for outputs)
- Network: Reliable internet connection to LLM providers

**Recommended Requirements**:

- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD
- Network: High-bandwidth, low-latency connection

### Operating System

Supported platforms:

- **Ubuntu 22.04 LTS** (Recommended)
- **RHEL/CentOS 8+**
- **Debian 11+**
- macOS 12+ (for development/testing)

### Python Environment

```bash
# Install Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
python3.12 --version
uv --version
```

### Application Installation

```bash
# 1. Create application directory
sudo mkdir -p /opt/pptx-agent
sudo chown $USER:$USER /opt/pptx-agent
cd /opt/pptx-agent

# 2. Clone repository (or deploy package)
git clone <repository-url> .
# OR: Copy built package
# uv pip install pptx-agent-*.whl

# 3. Install dependencies
uv sync --no-dev  # Production dependencies only

# 4. Create required directories
mkdir -p data/templates
mkdir -p data/outputs
mkdir -p logs
```

### File Permissions

```bash
# Set appropriate permissions
chmod 750 /opt/pptx-agent
chmod 640 /opt/pptx-agent/.env

# If running as service user
sudo chown -R pptx-agent:pptx-agent /opt/pptx-agent
```

## LLM Provider Configuration

### Primary Provider: IBM watsonx.ai

1. **Create watsonx.ai Account**:
   - Sign up at [https://www.ibm.com/cloud/watsonx-ai](https://www.ibm.com/cloud/watsonx-ai)
   - Create a project
   - Generate API key

2. **Configure Environment**:

   ```bash
   # /opt/pptx-agent/.env
   LLM_PROVIDER=watsonx
   LLM_MODEL=ibm/granite-13b-chat-v2
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   WATSONX_APIKEY=your-production-api-key
   WATSONX_PROJECT_ID=your-project-id
   ENVIRONMENT=production
   ```

3. **Verify Connection**:
   ```bash
   uv run python -c "from pptx_agent.config import get_config; print(get_config())"
   ```

### Fallback Provider: Anthropic Claude

1. **Create Anthropic Account**:
   - Sign up at [https://console.anthropic.com/](https://console.anthropic.com/)
   - Generate API key

2. **Configure Fallback**:

   ```bash
   # Add to .env
   ENABLE_FALLBACK=true
   FALLBACK_PROVIDER=anthropic
   FALLBACK_MODEL=claude-3-5-sonnet-20241022
   ANTHROPIC_API_KEY=sk-ant-api03-your-key
   ```

3. **Test Fallback**:
   ```bash
   # Temporarily disable primary provider to test fallback
   WATSONX_APIKEY=invalid uv run python -m pptx_agent.main --help
   ```

### Provider Best Practices

- **Rate Limits**: Monitor and respect provider rate limits
- **API Keys**: Rotate API keys quarterly
- **Cost Management**: Set up billing alerts
- **Redundancy**: Always configure fallback provider

## Security Configuration

### Environment Variables

**Never commit `.env` to version control!**

```bash
# Secure .env file
chmod 600 /opt/pptx-agent/.env
chown pptx-agent:pptx-agent /opt/pptx-agent/.env

# Use secrets management in production
# Example with AWS Secrets Manager:
aws secretsmanager get-secret-value --secret-id pptx-agent/watsonx-key \
  | jq -r .SecretString | grep -oP 'WATSONX_APIKEY=\K.*' > /tmp/apikey
```

### API Key Security

1. **Key Rotation**:

   ```bash
   # Rotate keys every 90 days
   # Keep old key active during rotation window
   # Update .env with new key
   # Verify service health
   # Deactivate old key
   ```

2. **Key Storage**:
   - Use secrets management service (AWS Secrets Manager, HashiCorp Vault)
   - Never log API keys
   - Mask keys in error messages

3. **Access Control**:
   ```bash
   # Limit file access
   sudo usermod -a -G pptx-agent deployment-user
   sudo chmod 640 .env
   ```

### Input Validation

The system includes built-in security features:

- **Prompt Injection Detection**: Automatically detects and sanitizes suspicious patterns
- **File Validation**: ZIP bomb protection, size limits, path traversal prevention
- **XML Security**: Protection against XXE and entity expansion attacks

### Network Security

```bash
# Firewall rules (example with ufw)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 443/tcp  # HTTPS (if exposing web interface)
sudo ufw enable

# Restrict outbound connections to LLM providers only
# (Implementation depends on your firewall/network setup)
```

## Monitoring and Logging

### Logging Configuration

```python
# Production logging setup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/pptx-agent/logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### Logfire Integration (Optional)

```bash
# Enable Logfire for LLM tracing
LOGFIRE_TOKEN=your-logfire-token
LOGFIRE_PROJECT_NAME=pptx-agent-prod

# View traces at https://logfire.pydantic.dev/
```

### Monitoring Metrics

Monitor these key metrics:

1. **Generation Success Rate**: Target ≥95%
2. **Average Generation Time**: Target <60s per presentation
3. **LLM API Response Time**: Track latency
4. **Error Rate**: Alert on >5% error rate
5. **Resource Usage**: CPU, memory, disk
6. **Cost**: LLM API costs per generation

### Health Checks

```bash
# Simple health check script
#!/bin/bash
# /opt/pptx-agent/healthcheck.sh

cd /opt/pptx-agent
uv run python -c "from pptx_agent.config import get_config; get_config()" \
  && echo "✓ Configuration OK" \
  || (echo "✗ Configuration failed" && exit 1)
```

### Log Rotation

```bash
# /etc/logrotate.d/pptx-agent
/opt/pptx-agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 pptx-agent pptx-agent
    sharedscripts
    postrotate
        systemctl reload pptx-agent || true
    endscript
}
```

## Performance Optimization

### Template Caching

```python
# Cache parsed templates
from functools import lru_cache
from pptx_agent.template_parser.parser import TemplateParser

@lru_cache(maxsize=10)
def get_cached_manifest(template_path: str):
    parser = TemplateParser()
    return parser.parse_template(template_path)
```

### Concurrency

```bash
# Process multiple presentations in parallel
parallel -j 4 'uv run python -m pptx_agent.main \
  --input {} \
  --template template.pptx \
  --output {.}.pptx' ::: input*.txt
```

### Resource Limits

```bash
# Systemd service with resource limits
# /etc/systemd/system/pptx-agent.service

[Service]
MemoryMax=2G
CPUQuota=200%
TasksMax=100
```

## Scaling Considerations

### Horizontal Scaling

For high-volume scenarios:

1. **Queue-Based Architecture**:

   ```
   Requests → Message Queue (RabbitMQ/SQS) → Worker Pool → Results
   ```

2. **Worker Process**:

   ```python
   # worker.py
   from celery import Celery
   from pptx_agent.pipeline import generate_presentation

   app = Celery('pptx-agent', broker='redis://localhost:6379')

   @app.task
   def generate_async(input_text, template_path, output_path):
       return generate_presentation(
           input_text=input_text,
           template_path=template_path,
           output_path=output_path,
           template_manifest=None,
           output_language="en",
       )
   ```

3. **Load Balancing**:
   - Deploy multiple worker instances
   - Use load balancer for API requests
   - Distribute across availability zones

### Vertical Scaling

- **CPU**: More cores for parallel processing
- **RAM**: Cache templates and intermediate results
- **Disk**: SSD for faster I/O
- **Network**: High-bandwidth for large presentations

## Backup and Disaster Recovery

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
# /opt/pptx-agent/backup.sh

BACKUP_DIR=/backup/pptx-agent
DATE=$(date +%Y%m%d)

# Backup templates
tar -czf $BACKUP_DIR/templates-$DATE.tar.gz /opt/pptx-agent/data/templates

# Backup configuration (excluding secrets)
cp /opt/pptx-agent/pyproject.toml $BACKUP_DIR/
cp /opt/pptx-agent/mise.toml $BACKUP_DIR/

# Backup logs
tar -czf $BACKUP_DIR/logs-$DATE.tar.gz /opt/pptx-agent/logs

# Rotate old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery

1. **Recovery Time Objective (RTO)**: < 1 hour
2. **Recovery Point Objective (RPO)**: < 24 hours

**Recovery Steps**:

```bash
# 1. Provision new server
# 2. Install dependencies
# 3. Restore from backup
cd /opt
tar -xzf /backup/pptx-agent/templates-latest.tar.gz

# 4. Restore configuration
cp /backup/pptx-agent/pyproject.toml /opt/pptx-agent/
cp /backup/pptx-agent/mise.toml /opt/pptx-agent/

# 5. Restore secrets from secrets manager
# 6. Verify health
/opt/pptx-agent/healthcheck.sh

# 7. Resume operations
```

## Troubleshooting

### Common Production Issues

#### Issue: High API Costs

**Symptoms**: Unexpected LLM API costs

**Solutions**:

1. Check `MAX_REQUESTS` and `MAX_RESPONSE_TOKENS` limits
2. Review generation patterns for efficiency
3. Implement request caching
4. Use cheaper models for simple content

#### Issue: Slow Generation

**Symptoms**: Presentations take >60s to generate

**Solutions**:

1. Check network latency to LLM provider
2. Verify template size (large templates slow parsing)
3. Monitor system resources (CPU/RAM)
4. Enable template caching

#### Issue: Provider Failures

**Symptoms**: Generation fails with provider errors

**Solutions**:

1. Verify API keys are valid
2. Check provider status page
3. Ensure fallback provider is configured
4. Review rate limits

#### Issue: Memory Leaks

**Symptoms**: Memory usage grows over time

**Solutions**:

1. Monitor with: `ps aux | grep python`
2. Check for unclosed file handles
3. Review template caching (LRU cache limits)
4. Restart service periodically

### Debug Mode

```bash
# Enable verbose logging
uv run python -m pptx_agent.main \
  --input input.txt \
  --template template.pptx \
  --output output.pptx \
  --verbose

# Check configuration
uv run python -c "from pptx_agent.config import get_config; import pprint; pprint.pprint(get_config().model_dump())"
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests pass (`mise run ci`)
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] Backup strategy tested
- [ ] Monitoring configured

### Deployment

- [ ] Application installed in `/opt/pptx-agent`
- [ ] Environment variables configured in `.env`
- [ ] API keys validated
- [ ] File permissions set correctly
- [ ] Log rotation configured
- [ ] Firewall rules applied

### Post-Deployment

- [ ] Health check passes
- [ ] Test generation successful
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Team trained on operations

### Production Verification

```bash
# 1. Verify installation
uv run python -m pptx_agent.main --help

# 2. Test generation
uv run python -m pptx_agent.main \
  --input tests/fixtures/sample_story_en.txt \
  --template templates/basic-template.pptx \
  --output /tmp/test-output.pptx

# 3. Verify output
ls -lh /tmp/test-output.pptx

# 4. Check logs
tail -f logs/app.log
```
