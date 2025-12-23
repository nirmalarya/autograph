# AutoGraph v3 - Disaster Recovery Plan

## Overview

This document outlines the disaster recovery (DR) strategy for AutoGraph v3, including Recovery Time Objective (RTO) and Recovery Point Objective (RPO) targets, procedures, and testing protocols.

## Executive Summary

- **RTO (Recovery Time Objective)**: 1 hour
- **RPO (Recovery Point Objective)**: 5 minutes
- **Testing Frequency**: Quarterly (every 3 months)
- **Last Tested**: [To be updated after first DR test]
- **Next Scheduled Test**: [To be scheduled]

## Recovery Objectives

### Recovery Time Objective (RTO): 1 Hour

The system must be restored to operational status within **1 hour** of a complete infrastructure failure.

**Breakdown:**
- Infrastructure provisioning: 15 minutes
- Database restore: 20 minutes
- Service deployment: 15 minutes
- Verification and testing: 10 minutes

### Recovery Point Objective (RPO): 5 Minutes

Maximum acceptable data loss is **5 minutes**. This is achieved through:
- Database backups every 24 hours
- MinIO bucket backups every 7 days
- Redis session data (acceptable loss: 5 minutes of session data)
- Real-time data in PostgreSQL write-ahead log (WAL)

## Critical Services

### Priority 1 (Must Recover First)
1. **PostgreSQL Database** - Contains all user data, diagrams, versions
2. **MinIO Object Storage** - Contains diagram files, exports, uploads
3. **Redis Cache** - Session management and real-time data

### Priority 2 (Recover Second)
4. **API Gateway** - Entry point for all requests
5. **Auth Service** - User authentication and authorization
6. **Diagram Service** - Core diagram management

### Priority 3 (Recover Last)
7. **AI Service** - AI-powered diagram generation
8. **Collaboration Service** - Real-time collaboration features
9. **Export Service** - Export functionality
10. **Git Service** - Git integration
11. **Integration Hub** - Third-party integrations
12. **SVG Renderer** - SVG rendering service
13. **Frontend** - User interface

## Backup Strategy

### Database Backups (PostgreSQL)

**Schedule:** Every 24 hours (automated)

**Retention:**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

**Backup Format:** Custom PostgreSQL dump format (pg_dump -Fc)

**Storage:**
- Primary: Local filesystem at `/tmp/autograph-backups/database/`
- Secondary: MinIO bucket `autograph-backups`

**Verification:** Each backup is automatically verified after creation

### MinIO Bucket Backups

**Schedule:** Every 7 days (automated)

**Buckets:**
- `diagrams` - Diagram canvas data
- `exports` - Exported files (PNG, SVG, PDF)
- `uploads` - User-uploaded files

**Retention:**
- Weekly backups: 4 weeks
- Monthly backups: 12 months

**Backup Format:** tar.gz archives with metadata

**Storage:**
- Primary: Local filesystem at `/tmp/autograph-backups/minio/`
- Secondary: MinIO bucket `minio-backups`

### Redis Data

**Strategy:** Redis data is ephemeral (sessions, cache)

**Acceptable Loss:** 5 minutes of session data

**Recovery:** Redis is restarted empty; users re-authenticate

**Notes:** Redis RDB snapshots can be enabled for persistent data if needed

## Disaster Scenarios

### Scenario 1: Complete Infrastructure Failure

**Symptoms:**
- All services unreachable
- Database connection failures
- Storage unavailable

**Recovery Steps:**

1. **Assess Damage** (5 minutes)
   ```bash
   # Check infrastructure status
   docker-compose ps
   docker ps -a
   
   # Check logs for errors
   docker-compose logs --tail=100
   ```

2. **Restore Infrastructure** (15 minutes)
   ```bash
   # Stop all containers
   docker-compose down
   
   # Remove volumes if corrupted
   docker volume rm $(docker volume ls -q | grep autograph)
   
   # Start infrastructure services
   docker-compose up -d postgres redis minio
   
   # Wait for health checks
   sleep 30
   ```

3. **Restore Database** (20 minutes)
   ```bash
   # List available backups
   curl http://localhost:8080/api/admin/backup/list
   
   # Restore latest backup
   curl -X POST "http://localhost:8080/api/admin/backup/restore?backup_name=scheduled_backup_YYYYMMDD_HHMMSS"
   
   # Verify database integrity
   docker exec autograph-postgres psql -U postgres -d autograph -c "\dt"
   ```

4. **Restore MinIO Buckets** (15 minutes)
   ```bash
   # List available backups
   curl http://localhost:8080/api/admin/minio/backup/list
   
   # Restore each bucket
   curl -X POST "http://localhost:8080/api/admin/minio/backup/restore?backup_name=scheduled_diagrams_YYYYMMDD_HHMMSS&target_bucket=diagrams"
   curl -X POST "http://localhost:8080/api/admin/minio/backup/restore?backup_name=scheduled_exports_YYYYMMDD_HHMMSS&target_bucket=exports"
   curl -X POST "http://localhost:8080/api/admin/minio/backup/restore?backup_name=scheduled_uploads_YYYYMMDD_HHMMSS&target_bucket=uploads"
   ```

5. **Start Application Services** (15 minutes)
   ```bash
   # Start all microservices
   docker-compose up -d
   
   # Monitor startup
   docker-compose ps
   docker-compose logs -f
   ```

6. **Verify System** (10 minutes)
   ```bash
   # Check health endpoints
   curl http://localhost:8080/health
   curl http://localhost:8085/health  # Auth service
   curl http://localhost:8082/health  # Diagram service
   
   # Verify database connectivity
   curl http://localhost:8080/api/users/me
   
   # Test diagram creation
   curl -X POST http://localhost:8080/api/diagrams \
     -H "Content-Type: application/json" \
     -d '{"name": "DR Test Diagram"}'
   ```

**Total Time:** ~60 minutes (within RTO)

### Scenario 2: Database Corruption

**Symptoms:**
- PostgreSQL connection errors
- Data integrity issues
- Query failures

**Recovery Steps:**

1. **Stop Application Services** (2 minutes)
   ```bash
   docker-compose stop api-gateway auth-service diagram-service
   ```

2. **Restore Database** (20 minutes)
   ```bash
   # Drop existing database
   docker exec autograph-postgres psql -U postgres -c "DROP DATABASE IF EXISTS autograph;"
   
   # Restore from backup
   curl -X POST "http://localhost:8080/api/admin/backup/restore?backup_name=scheduled_backup_YYYYMMDD_HHMMSS"
   ```

3. **Restart Services** (5 minutes)
   ```bash
   docker-compose start api-gateway auth-service diagram-service
   ```

**Total Time:** ~30 minutes

### Scenario 3: MinIO Data Loss

**Symptoms:**
- File not found errors
- Missing diagrams or exports
- S3 bucket errors

**Recovery Steps:**

1. **Identify Missing Data** (5 minutes)
   ```bash
   # List current buckets
   curl http://localhost:8080/api/admin/minio/buckets
   
   # Check bucket contents
   docker exec autograph-minio mc ls minio/diagrams
   ```

2. **Restore Buckets** (15 minutes)
   ```bash
   # Restore specific bucket
   curl -X POST "http://localhost:8080/api/admin/minio/backup/restore?backup_name=scheduled_diagrams_YYYYMMDD_HHMMSS&target_bucket=diagrams&overwrite=false"
   ```

**Total Time:** ~20 minutes

## DR Testing Protocol

### Quarterly DR Test Schedule

**Frequency:** Every 3 months (January, April, July, October)

**Test Duration:** 2-3 hours

**Test Window:** Off-peak hours (weekends or evenings)

### DR Test Procedure

1. **Pre-Test Preparation** (30 minutes)
   - Schedule test window
   - Notify stakeholders
   - Document current system state
   - Create fresh backups
   - Prepare rollback plan

2. **Simulated Failure** (5 minutes)
   ```bash
   # Execute DR simulation test
   python test_disaster_recovery.py
   ```

3. **Recovery Execution** (60 minutes)
   - Follow documented recovery procedures
   - Time each step
   - Document any issues or deviations
   - Measure RTO compliance

4. **Verification** (30 minutes)
   - Verify all services are healthy
   - Test critical user workflows
   - Check data integrity
   - Measure RPO compliance (data loss)

5. **Post-Test Review** (30 minutes)
   - Document test results
   - Update DR plan based on lessons learned
   - Update RTO/RPO if needed
   - Plan remediation for any issues

### Test Metrics to Capture

- **Actual RTO:** Time from failure to full recovery
- **Actual RPO:** Amount of data lost
- **Service Recovery Time:** Time for each service to become healthy
- **Database Restore Time:** Time to restore database
- **MinIO Restore Time:** Time to restore object storage
- **Issues Encountered:** Any problems during recovery
- **Action Items:** Improvements needed

### Success Criteria

- [ ] All services recovered within 1 hour (RTO)
- [ ] Data loss < 5 minutes (RPO)
- [ ] All health checks passing
- [ ] User authentication working
- [ ] Diagram creation/retrieval working
- [ ] Real-time collaboration working
- [ ] Export functionality working
- [ ] No data corruption detected

## Automation

### Automated Backup Scripts

**Database Backup:**
- Script: `shared/python/backup.py` (DatabaseBackupManager)
- Schedule: Every 24 hours via background task in API Gateway
- Monitoring: Logs to structured JSON logs

**MinIO Backup:**
- Script: `shared/python/backup.py` (MinIOBucketBackupManager)
- Schedule: Every 7 days via background task in API Gateway
- Monitoring: Logs to structured JSON logs

### Automated DR Testing

**Test Script:** `test_disaster_recovery.py`

**Capabilities:**
- Simulate complete infrastructure failure
- Execute automated recovery
- Measure RTO/RPO
- Generate test report

**Usage:**
```bash
python test_disaster_recovery.py --simulate
```

## Monitoring and Alerting

### Critical Alerts

1. **Backup Failures**
   - Alert when scheduled backup fails
   - Alert when backup size is unusually small
   - Alert when backup verification fails

2. **Service Health**
   - Alert when service is unhealthy for > 5 minutes
   - Alert when database connection fails
   - Alert when MinIO is unreachable

3. **Storage Capacity**
   - Alert when disk usage > 80%
   - Alert when backup storage is running low
   - Alert when MinIO bucket quota exceeded

### Alert Channels

- **Console Logs:** All alerts logged to stdout
- **File Logs:** Critical alerts written to `/var/log/autograph/alerts.log`
- **Email:** (Optional) Configure SMTP for email alerts
- **Slack:** (Optional) Configure webhook for Slack notifications

## Roles and Responsibilities

### DR Coordinator
- Declares disaster
- Coordinates recovery efforts
- Communicates with stakeholders
- Makes decisions on recovery priorities

### Technical Lead
- Executes recovery procedures
- Monitors system health
- Troubleshoots issues
- Validates recovery success

### Operations Team
- Assists with infrastructure provisioning
- Monitors backup systems
- Maintains DR documentation
- Conducts DR tests

### Communication Lead
- Notifies users of outage
- Provides status updates
- Manages external communications
- Documents incident timeline

## Contact Information

### Emergency Contacts

**DR Coordinator:** [Name] - [Phone] - [Email]

**Technical Lead:** [Name] - [Phone] - [Email]

**Operations Team:** [Team Email] - [Slack Channel]

**Escalation Path:**
1. Technical Lead (0-30 minutes)
2. DR Coordinator (30-60 minutes)
3. Executive Team (60+ minutes)

## Documentation Updates

### Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-23 | 1.0 | Initial DR plan created | AutoGraph Team |

### Review Schedule

- **Quarterly:** After each DR test
- **Annually:** Comprehensive review and update
- **Ad-hoc:** After any production incident

## Appendix

### A. Backup File Locations

**Database Backups:**
- Local: `/tmp/autograph-backups/database/`
- MinIO: `s3://autograph-backups/database/`

**MinIO Backups:**
- Local: `/tmp/autograph-backups/minio/`
- MinIO: `s3://minio-backups/`

### B. Service Dependencies

```
Frontend → API Gateway → Auth Service → PostgreSQL
                      → Diagram Service → PostgreSQL
                                       → MinIO
                      → AI Service
                      → Collaboration Service → Redis
```

### C. Health Check URLs

| Service | URL | Expected Response |
|---------|-----|-------------------|
| API Gateway | http://localhost:8080/health | {"status": "healthy"} |
| Auth Service | http://localhost:8085/health | {"status": "healthy"} |
| Diagram Service | http://localhost:8082/health | {"status": "healthy"} |
| AI Service | http://localhost:8084/health | {"status": "healthy"} |
| PostgreSQL | docker exec autograph-postgres pg_isready | accepting connections |
| Redis | docker exec autograph-redis redis-cli ping | PONG |
| MinIO | curl http://localhost:9000/minio/health/live | 200 OK |

### D. Common Issues and Solutions

**Issue:** Database restore fails with "database already exists"

**Solution:** Drop database first:
```bash
docker exec autograph-postgres psql -U postgres -c "DROP DATABASE IF EXISTS autograph;"
```

**Issue:** MinIO bucket restore fails with "bucket already exists"

**Solution:** Use overwrite flag:
```bash
curl -X POST "http://localhost:8080/api/admin/minio/backup/restore?backup_name=backup&target_bucket=diagrams&overwrite=true"
```

**Issue:** Services fail to start after recovery

**Solution:** Check logs and restart in order:
```bash
docker-compose logs --tail=100
docker-compose restart postgres redis minio
docker-compose restart api-gateway auth-service
docker-compose restart diagram-service
```

### E. DR Test Checklist

Pre-Test:
- [ ] Backup current system state
- [ ] Schedule test window
- [ ] Notify stakeholders
- [ ] Prepare rollback plan
- [ ] Document baseline metrics

During Test:
- [ ] Simulate failure
- [ ] Time recovery steps
- [ ] Document issues
- [ ] Take screenshots
- [ ] Monitor logs

Post-Test:
- [ ] Verify all services healthy
- [ ] Test critical workflows
- [ ] Calculate RTO/RPO
- [ ] Update documentation
- [ ] Schedule next test

### F. Lessons Learned

*(To be updated after each DR test)*

**Test Date:** [Date]

**What Went Well:**
- [Item]

**What Went Wrong:**
- [Item]

**Action Items:**
- [Item]

---

**Document Version:** 1.0

**Last Updated:** December 23, 2025

**Next Review:** March 23, 2026

**Owner:** AutoGraph v3 Operations Team
