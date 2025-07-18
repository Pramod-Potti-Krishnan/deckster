# Deploy Fixes Command - Generic Production Debugging Guide

## Purpose
This command provides a systematic approach to debug and resolve production issues across any deployment platform, technology stack, or application type. It helps coordinate between frontend, backend, and infrastructure teams to efficiently identify root causes and implement fixes.

## Pre-Incident Preparation Checklist
- [ ] Monitoring/APM tools configured (DataDog, New Relic, CloudWatch, etc.)
- [ ] Log aggregation setup (ELK, Splunk, CloudWatch Logs, etc.)
- [ ] Error tracking integrated (Sentry, Rollbar, Bugsnag, etc.)
- [ ] Runbooks documented for common scenarios
- [ ] On-call rotation established with escalation paths
- [ ] Access credentials secured and available

## Usage
When production issues occur, gather the following information based on your application type:

### Required Information to Provide:

#### 1. **Client-Side Logs** (if applicable)
- Browser Console (F12) - Errors, warnings, network failures
- Mobile App Logs - Crash reports, debug logs
- Desktop App Logs - Application logs, system events

#### 2. **Server/Platform Logs**
Choose relevant platform:
- **Cloud Platforms**: AWS CloudWatch, GCP Stackdriver, Azure Monitor
- **PaaS Providers**: Heroku, Railway, Render, Fly.io logs
- **Container Platforms**: Kubernetes logs, Docker logs, ECS logs
- **Traditional Hosting**: Apache/Nginx access/error logs

#### 3. **User Context**
- Exact user actions leading to the issue
- User type/role (authenticated, admin, free/paid tier)
- Device/Browser/OS information
- Geographic location (if relevant)
- Time of occurrence (with timezone)

#### 4. **Expected vs Actual Behavior**
- What should have happened
- What actually happened
- Error messages displayed to user
- Screenshots/recordings if available

### Example Template:
```
/deploy-fixes

**Client-Side Logs:**
```
[ERROR] TypeError: Cannot read properties of undefined (reading '[PROPERTY]')
    at [FUNCTION_NAME] ([FILE]:line:column)
[INFO] API call to /api/[ENDPOINT] - Status: 200
[ERROR] Network request failed: [ERROR_MESSAGE]
```

**Server/Platform Logs:**
```
[TIMESTAMP] INFO: [SERVICE_NAME] - Request received: [ENDPOINT]
[TIMESTAMP] ERROR: [SERVICE_NAME] - [ERROR_TYPE]: [ERROR_MESSAGE]
[TIMESTAMP] DEBUG: Database query execution time: [TIME]ms
```

**User Context:** 
- User Role: [authenticated/guest/admin]
- Action: [Specific action taken]
- Browser/App: [Chrome 120/iOS App v2.1]
- Location: [Country/Region]
- Time: [2024-01-15 14:30 UTC]

**Expected:** [Clear description of intended behavior]
**Actual:** [What happened instead, including any error messages]
```

### Domain-Specific Examples:

#### E-commerce Example:
```
**Issue**: Checkout process failing for international customers
**Client Error**: "PaymentMethodError: Invalid currency"
**Server Error**: "Payment gateway timeout after 30s"
**User Context**: Canadian user trying to purchase with USD pricing
```

#### SaaS Application Example:
```
**Issue**: Data export feature returning empty files
**Client Error**: "Download started but file size is 0 bytes"
**Server Error**: "Memory allocation failed: heap out of memory"
**User Context**: Enterprise user exporting 6 months of analytics data
```

#### Mobile App Example:
```
**Issue**: App crashes on startup after update
**Client Error**: "Fatal Exception: NSInvalidArgumentException"
**Server Error**: "API version mismatch: client v2.0, server expects v1.9"
**User Context**: Users who auto-updated to latest app version
```

## Claude's Response Process

When this command is used, Claude will:

### 1. **Root Cause Analysis**
- Analyze F12 console logs to identify frontend issues
- Examine Railway logs to identify backend issues  
- Correlate user input with error patterns
- Identify the sequence of events leading to the failure

### 2. **Issue Classification Framework**

#### Frontend Issues
- **Rendering/UI**: Component crashes, layout issues, browser compatibility
- **State Management**: Redux/MobX/Context errors, data synchronization
- **Network**: API calls, timeouts, CORS issues
- **Performance**: Memory leaks, slow rendering, bundle size

#### Backend Issues  
- **API/Service**: Endpoint failures, timeout errors, rate limiting
- **Database**: Query failures, connection pool exhaustion, deadlocks
- **Processing**: Business logic errors, data validation failures
- **External Services**: Third-party API failures, webhook issues

#### Integration Issues
- **Protocol Mismatches**: REST/GraphQL/WebSocket/gRPC incompatibilities
- **Data Format**: Schema mismatches, serialization errors
- **Authentication**: Token expiry, permission errors, SSO failures
- **Versioning**: API version conflicts, backward compatibility

#### Infrastructure Issues
- **Deployment**: Build failures, environment variables, secrets management
- **Scaling**: Resource limits, auto-scaling failures, load balancer issues
- **Network**: DNS failures, SSL/TLS errors, firewall rules
- **Platform**: Container crashes, orchestration failures, service mesh issues

### 3. **Priority Assessment Matrix**

| Priority | Severity | User Impact | Business Impact | Response Time |
|----------|----------|-------------|-----------------|---------------|
| **P0** | Critical | All users blocked | Revenue loss, compliance risk | < 15 minutes |
| **P1** | High | Major features broken | Significant user churn risk | < 1 hour |
| **P2** | Medium | Some features affected | Moderate inconvenience | < 4 hours |
| **P3** | Low | Minor/cosmetic issues | Minimal impact | < 24 hours |

#### Escalation Triggers
- P0 after 30 min → VP Engineering + On-call Manager
- P1 after 2 hours → Engineering Manager + Product Owner  
- Customer complaint volume > 50 → Upgrade priority level
- Security implications → Always treat as P0/P1

### 4. **Task List Templates**

#### Frontend Task Template:
```markdown
- [ ] **[PRIORITY]** - [Component/Feature]: [Specific Issue]
  - Root Cause: [Technical explanation]
  - Fix: [Proposed solution]
  - Testing: [How to verify]
  - Rollback: [If fix fails]
```

#### Backend Task Template:
```markdown
- [ ] **[PRIORITY]** - [Service/API]: [Specific Issue]  
  - Affected Endpoints: [List endpoints]
  - Database Impact: [Yes/No - details]
  - Dependencies: [External services affected]
  - Monitoring: [Metrics to watch]
```

#### Infrastructure Task Template:
```markdown
- [ ] **[PRIORITY]** - [Platform/Service]: [Specific Issue]
  - Environment: [Prod/Staging/Dev]
  - Resources: [CPU/Memory/Disk/Network]
  - Configuration: [What needs changing]
  - Rollout Plan: [Canary/Blue-Green/Rolling]
```

### Generic Task Examples by Category:

#### Frontend Tasks:
- [ ] **P0** - Error Handling: Add try-catch blocks around [COMPONENT]
- [ ] **P1** - State Management: Fix race condition in [STATE_STORE]
- [ ] **P2** - Performance: Implement lazy loading for [FEATURE]
- [ ] **P3** - UX: Add loading indicators for async operations

#### Backend Tasks:
- [ ] **P0** - API: Fix timeout in [ENDPOINT] (current: Xs, target: <Ys)
- [ ] **P1** - Database: Add connection pooling (current connections: X)
- [ ] **P2** - Caching: Implement Redis cache for [DATA_TYPE]
- [ ] **P3** - Logging: Add structured logging to [SERVICE]

#### Infrastructure Tasks:
- [ ] **P0** - Scaling: Increase instance count from X to Y
- [ ] **P1** - Monitoring: Add alerts for [METRIC] threshold
- [ ] **P2** - Security: Rotate [CREDENTIALS/KEYS]
- [ ] **P3** - Optimization: Update [DEPENDENCY] version

### 5. **Implementation Plan**

#### Phase 1: Immediate Response (0-30 minutes)
1. **Acknowledge Incident**
   - Create incident channel/war room
   - Notify stakeholders
   - Start incident timeline documentation

2. **Triage & Contain**
   - Implement temporary fixes/workarounds
   - Scale resources if needed
   - Enable feature flags to disable problematic features

#### Phase 2: Root Cause Analysis (30 min - 2 hours)
1. **Data Collection**
   ```bash
   # Example commands for different platforms
   kubectl logs -f deployment/[APP_NAME] --tail=1000  # Kubernetes
   heroku logs --tail --app=[APP_NAME]                # Heroku  
   aws logs tail /aws/lambda/[FUNCTION_NAME]          # AWS Lambda
   docker logs -f [CONTAINER_ID]                      # Docker
   ```

2. **Analysis Tools**
   - APM dashboards (New Relic, DataDog, AppDynamics)
   - Distributed tracing (Jaeger, Zipkin, AWS X-Ray)
   - Database query analyzers
   - Network traffic analysis (Wireshark, tcpdump)

#### Phase 3: Fix Implementation
1. **Development Process**
   - Create feature branch: `hotfix/[INCIDENT_ID]-[description]`
   - Write tests to reproduce issue
   - Implement fix with proper error handling
   - Code review (even for hotfixes)

2. **Deployment Strategy**
   ```yaml
   # Example deployment strategies
   canary:
     - Deploy to 5% of traffic
     - Monitor for 15 minutes
     - Gradual rollout: 25% → 50% → 100%
   
   blue_green:
     - Deploy to green environment
     - Smoke test all critical paths
     - Switch traffic at load balancer
     - Keep blue environment for quick rollback
   ```

### 6. **Team Coordination Matrix**

| Team | Primary Focus | Key Metrics | Communication |
|------|--------------|-------------|---------------|
| **Frontend** | UI stability, UX | Error rates, load times | #incident-frontend |
| **Backend** | API reliability | Response times, error rates | #incident-backend |
| **Infrastructure** | Platform stability | CPU, memory, disk I/O | #incident-infra |
| **Database** | Data integrity | Query times, locks | #incident-database |
| **Security** | Access & vulnerabilities | Auth failures, suspicious activity | #incident-security |

#### Cross-Team Sync Points
- Every 30 minutes during P0 incidents
- Every 2 hours during P1 incidents
- Daily standup for P2/P3 issues

## Expected Outcomes

After using this command, you should have:
-  Clear understanding of what went wrong
-  Prioritized list of tasks for each team
-  Communication plan between frontend and backend teams
-  Testing strategy to verify fixes
-  Documentation of the debugging process

## Best Practices

1. **Provide Complete Information**: Include all relevant logs, not just error messages
2. **Be Specific**: Exact user actions, timestamps, affected features
3. **Include Context**: What was working before, what changed recently
4. **Multiple Scenarios**: If the issue happens in different situations, include all
5. **Environment Details**: Production vs staging, browser versions, user types

## Follow-up Actions

After Claude provides the analysis and task lists:
1. Review and prioritize the tasks
2. Assign tasks to appropriate team members
3. Create tracking issues/tickets
4. Begin implementation starting with P0 tasks
5. Regular check-ins to ensure coordination
6. Document lessons learned for future issues

## Comprehensive Checklists

### During Incident Checklist
- [ ] Incident commander assigned
- [ ] Communication channels established
- [ ] Stakeholders notified (internal & external)
- [ ] Status page updated
- [ ] Temporary workarounds implemented
- [ ] Monitoring dashboards open
- [ ] Logs being collected and analyzed
- [ ] Timeline documentation started
- [ ] Customer support briefed
- [ ] Rollback plan ready if needed

### Fix Verification Checklist
- [ ] Unit tests written and passing
- [ ] Integration tests cover the scenario
- [ ] Load testing completed (for performance issues)
- [ ] Security review done (if applicable)
- [ ] Code reviewed by senior engineer
- [ ] Deployment plan documented
- [ ] Rollback tested
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Customer communication prepared

### Post-Incident Checklist
- [ ] Post-mortem scheduled within 48 hours
- [ ] Timeline documented with all actions
- [ ] Root cause analysis completed
- [ ] Action items assigned with deadlines
- [ ] Runbook created/updated
- [ ] Monitoring improved
- [ ] Tests added to prevent regression
- [ ] Knowledge shared with team
- [ ] Customer follow-up completed
- [ ] Metrics dashboard updated

## Monitoring & Observability

### Key Metrics to Track
```yaml
availability:
  - Uptime percentage
  - Error rate by endpoint
  - Success rate by feature

performance:
  - Response time (p50, p95, p99)
  - Database query time
  - API latency
  - Page load time

business:
  - Transaction success rate
  - User journey completion
  - Revenue impact
  - Customer satisfaction

infrastructure:
  - CPU/Memory utilization
  - Disk I/O
  - Network throughput
  - Container restart count
```

### Recommended Monitoring Stack
1. **Metrics**: Prometheus + Grafana, DataDog, New Relic
2. **Logs**: ELK Stack, Splunk, Sumo Logic
3. **Traces**: Jaeger, Zipkin, AWS X-Ray
4. **Errors**: Sentry, Rollbar, Bugsnag
5. **Uptime**: Pingdom, StatusCake, UptimeRobot

### Alert Configuration Template
```yaml
alert: HighErrorRate
expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
for: 5m
labels:
  severity: critical
  team: backend
annotations:
  summary: "High error rate detected"
  description: "Error rate is {{ $value | humanizePercentage }} for last 5 minutes"
  runbook: "https://wiki.company.com/runbooks/high-error-rate"
```

## Communication Templates

### Incident Notification
```
🚨 INCIDENT: [Title]
Severity: P[0-3]
Start Time: [Timestamp]
Impact: [User-facing description]
Status: Investigating | Identified | Monitoring | Resolved

Current Actions:
- [What's being done]

Next Update: [Time]
```

### Status Page Update
```
[Service Name] - [Degraded Performance | Partial Outage | Major Outage]

We are currently experiencing [issue description]. 
Affected Features: [List]
Workaround: [If available]

Updates will be provided every [30] minutes.
```

### Post-Incident Customer Communication
```
Subject: [Incident] - Post-Incident Report

On [Date], we experienced [brief description] affecting [impact].

What Happened:
[Root cause explanation in simple terms]

What We Did:
[Actions taken to resolve]

What We're Doing to Prevent This:
[Future prevention measures]

We apologize for any inconvenience and appreciate your patience.
```

## Platform-Specific Debugging Commands

### AWS
```bash
# CloudWatch Logs
aws logs tail /aws/lambda/[function-name] --follow
aws logs filter-log-events --log-group-name [group] --start-time [epoch]

# ECS/Fargate
aws ecs describe-tasks --cluster [cluster] --tasks [task-arn]
aws logs get-log-events --log-group-name /ecs/[service]

# RDS
aws rds describe-db-log-files --db-instance-identifier [instance]
aws rds download-db-log-file-portion --db-instance-identifier [instance] --log-file-name error/mysql-error.log
```

### Google Cloud
```bash
# Cloud Logging
gcloud logging read "resource.type=k8s_container AND severity>=ERROR" --limit 50
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=[name]"

# Cloud Run
gcloud run services logs read [service-name] --limit 100
```

### Kubernetes
```bash
# Pod logs
kubectl logs -f [pod-name] -c [container-name] --tail=100
kubectl logs -l app=[app-name] --all-containers=true

# Events
kubectl get events --sort-by='.lastTimestamp' -n [namespace]

# Debugging
kubectl describe pod [pod-name]
kubectl exec -it [pod-name] -- /bin/bash
```

---

This command provides a comprehensive framework for handling production incidents across any technology stack or deployment platform, ensuring systematic debugging and efficient resolution.