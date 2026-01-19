---
description:
  Emergency procedures and incident response for LUXORliving integration
---

# Incident Response Runbook

## Quick Reference

| Severity             | Response Time | Examples                                           |
| -------------------- | ------------- | -------------------------------------------------- |
| 🔴 **P0 - Critical** | <1 hour       | Auth broken, crash on startup, all devices offline |
| 🟠 **P1 - High**     | <4 hours      | Major feature broken, workaround exists            |
| 🟡 **P2 - Medium**   | <24 hours     | Minor bug, UI issue, performance degradation       |
| 🟢 **P3 - Low**      | Best effort   | Documentation typo, enhancement request            |

---

## Severity Classification

### 🔴 P0 - Critical

**Definition:** Integration completely broken, users can't control devices or HA
breaks

**Examples:**

- Integration fails to load on startup
- Circuit breaker stuck in OPEN state
- Coordinator crashes on every poll
- All entities become unavailable
- Configuration breaks HA on reload

**Response:**

1. **Acknowledge** (within 30 min): Comment on GitHub issue
2. **Assess Impact:** How many users? All versions or specific?
3. **Evaluate Options:**
   - Option A: Rollback last release
   - Option B: Hotfix if recent commit introduced issue
   - Option C: Emergency patch if config issue
4. **Implement Solution:**
   - Test on remote HA (100.97.159.88)
   - Create fix in `hotfix/` branch
   - Deploy with testing
5. **Release:** Hotfix within 4 hours
6. **Post-Incident:** Review root cause within 24 hours

**Example Scenario:**

```
USER: "Integration won't load, HA errors: ModuleNotFoundError"
RESPONSE:
1. Check git log - find breaking import change
2. Identify commit that broke it
3. Create hotfix/import-fix branch
4. Revert problematic change
5. Test locally + remote HA
6. Release v0.6.1 hotfix
7. Post: "Fixed in v0.6.1, thanks for reporting!"
```

### 🟠 P1 - High

**Definition:** Major feature broken, workaround exists, users frustrated

**Examples:**

- Dimming broken but on/off works
- Cover position reading incorrect
- Sensors only update on restart
- Auth repair flow not triggering

**Response:**

1. Create GitHub issue (label: `bug`, `P1`)
2. Reproduce issue locally
3. Investigate root cause
4. Develop fix with test coverage
5. Include in next release (or hotfix if urgent)
6. Communicate timeline to users

**SLA:** Acknowledge in <4 hours, fix in <1 week

### 🟡 P2 - Medium

**Definition:** Minor bug, limited impact, users can work around

**Examples:**

- Entity name incorrect
- UI label typo
- Performance regression (5-10% slower)
- Warning in logs

**Response:**

1. Create GitHub issue (label: `bug`, `P2`)
2. Add to next release milestone
3. Include in CHANGELOG
4. No urgent action needed

**SLA:** Fix in next scheduled release

### 🟢 P3 - Low

**Definition:** Cosmetic issue, feature request, no user impact

**Examples:**

- Documentation typo
- Translation missing
- README outdated
- Feature enhancement idea

**Response:**

1. Create GitHub issue (label: `enhancement`)
2. Community can contribute
3. No timeline commitment

---

## Emergency Procedures

### Emergency 1: Rollback Release

**When:** Previous release is broken, current release has critical bug

**Steps:**

```bash
# 1. Identify broken version
VERSION="v0.6.0"

# 2. Delete GitHub release
gh release delete "$VERSION" -y

# 3. Delete git tag (local + remote)
git tag -d "$VERSION"
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin ":refs/tags/$VERSION"

# 4. Verify last version still works
gh release list | head -5

# 5. Notify users (GitHub issue)
echo "⚠️ EMERGENCY ROLLBACK: v0.6.0 removed due to critical bug
Please update to v0.5.4.3 (latest stable)
v0.6.1 hotfix coming in 2 hours"
```

**Post-Rollback:**

- Document root cause
- Create fix + test
- Release hotfix version

---

### Emergency 2: Hotfix Release

**When:** Critical bug in latest release, needs immediate fix

**Steps:**

```bash
# 1. Create hotfix branch from last stable tag
LAST_VERSION=$(gh release list | head -1 | awk '{print $1}')
git checkout -b hotfix/critical-fix "$LAST_VERSION"

# 2. Identify and cherry-pick fix commit
# Option A: Commit exists on main
git log main --oneline | head -10
git cherry-pick <commit-sha>

# Option B: Fix doesn't exist, create it
# Edit file → git add → git commit

# 3. Verify tests still pass
python -m pytest tests/ -v

# 4. Update version (patch increment)
# manifest.json: "0.6.1" (from 0.6.0)
# CHANGELOG.md: Add entry

# 5. Commit + tag
git add -A
git commit -m "Hotfix: Brief description of fix"
git tag -a v0.6.1 -m "Hotfix: Critical bug fix"

# 6. Push to remote
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin hotfix/critical-fix
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin v0.6.1

# 7. Create release
gh release create v0.6.1 \
  --title "v0.6.1 - Critical Hotfix" \
  --notes "Fixes: [description of fix]" \
  --latest

# 8. Merge back to main
git checkout main
git merge hotfix/critical-fix
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin main

# 9. Clean up
git branch -d hotfix/critical-fix
```

**Post-Release:**

- Announce in README
- Update CHANGELOG
- Thank contributors

---

### Emergency 3: Circuit Breaker Stuck

**When:** Circuit breaker opens and won't recover

**Symptoms:**

```
ERROR: Circuit breaker OPEN, rejecting calls
(stuck for >timeout seconds)
```

**Diagnosis:**

```bash
# 1. Check HA logs
grep "circuit" /config/home-assistant.log | tail -20

# 2. Check gateway connectivity
ping <gateway-ip>  # Should respond

# 3. Check firewall
curl -k https://<gateway-ip>:3671/

# 4. Restart gateway via HA UI
# Settings → Devices & Services → LUXORliving → Health endpoint
curl http://localhost:8123/api/luxor_living/health
```

**Recovery Steps:**

```bash
# Option A: Reload integration
# HA UI → Settings → Devices & Services → LUXORliving → ⋮ → Reload

# Option B: Restart Home Assistant
sudo systemctl restart homeassistant
# or via HA UI → Settings → System → Restart

# Option C: Manual coordinator reset (if stuck)
# Not recommended - only as last resort
# Edit coordinator.py _async_update_data() to clear failure count
```

---

### Emergency 4: Config Flow Frozen

**When:** User can't complete setup, stuck in config flow

**Symptoms:**

```
- "Add integration" button does nothing
- Form submission hangs
- Timeout errors
```

**Debug:**

```bash
# 1. Check browser console for errors
# Press F12 → Console tab

# 2. Check HA system log
grep "config_flow" /config/home-assistant.log | tail -50

# 3. Check LXP file validity
python custom_components/luxor_living/lxp_parser.py \
  /config/luxor/project.lxp  # Should parse without error

# 4. Verify gateway is reachable
curl -k -u <user>:<pass> https://<gateway-ip>:3671/status
```

**Recovery:**

```bash
# Option A: Clear browser cache
# Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)

# Option B: Reload HA browser
# Ctrl+F5 (force reload)

# Option C: Restart HA backend
sudo systemctl restart homeassistant
```

---

## Communication Templates

### User Notification - Critical Issue

```markdown
## 🚨 Critical Issue Identified

**Severity:** P0 - Integration May Not Work **Affected:** v0.6.0 **Status:**
INVESTIGATING

### What Happened

[Brief description of issue]

### What We're Doing

- [Investigating root cause]
- [Developing fix]
- [Testing solution]

### What You Should Do

**Immediate action** (optional): Downgrade to v0.5.4.3

- Settings → Devices & Services → LUXORliving → ...

**ETA for fix:** ~2 hours

### Updates

- 10:00 UTC: Issue identified, working on fix
- 10:30 UTC: Fix ready, testing
- 11:00 UTC: v0.6.1 hotfix released

Follow this issue for updates!
```

### User Notification - Issue Resolved

```markdown
## ✅ Issue Resolved

**Severity:** P0 - Critical Bug **Affected:** v0.6.0 **Fixed in:** v0.6.1

### Root Cause

[Technical explanation of what went wrong]

### Solution

[What we fixed]

### What to Do

1. Update to v0.6.1 (Settings → Devices & Services → Custom integrations)
2. Reload integration
3. Report if issue persists

### Prevention

[What we'll do to prevent this in future]

Thanks for your patience! 🙏
```

### Internal - Post-Incident Review

```markdown
## Post-Incident Review: Issue Name

**Date:** 2026-01-11 **Severity:** P0 **Duration:** 1 hour **Users Affected:**
~50

### Timeline

- 10:00 UTC: Issue reported
- 10:15 UTC: Root cause identified
- 10:30 UTC: Fix ready
- 11:00 UTC: Release published

### Root Cause

[Technical details]

### Preventions

- [ ] Add test to prevent this
- [ ] Improve error handling
- [ ] Update documentation
- [ ] Code review checklist

### Action Items

- [ ] Assign owner for follow-up
- [ ] Schedule implementation
- [ ] Update runbook
```

---

## Monitoring & Detection

### Health Endpoint

```bash
# Check integration health
curl http://localhost:8123/api/luxor_living/health | jq

# Response example:
{
  "status": "healthy",  # or "degraded" / "unhealthy"
  "connection": "connected",
  "coordinator_state": "synced",
  "entities_count": 27,
  "last_update": "2026-01-11T10:00:00Z",
  "circuit_breaker_state": "closed"
}
```

### Performance Benchmark

```bash
# Run benchmark to detect regressions
curl -X POST http://localhost:8123/api/luxor_living/benchmark | jq

# Check for slowdowns (compare to baseline)
```

### HA Logs

```bash
# Enable debug logging for troubleshooting
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.luxor_living: debug

# Then check logs
tail -f /config/home-assistant.log | grep luxor_living
```

---

## Prevention Checklist

### Before Every Release

- [ ] All tests passing (pytest)
- [ ] Coverage ≥75%
- [ ] Code review completed
- [ ] Version bumped (manifest.json)
- [ ] CHANGELOG updated
- [ ] README updated (if feature changes)
- [ ] Documentation reviewed
- [ ] Breaking changes documented
- [ ] Migration guide prepared (if needed)

### After Release

- [ ] GitHub release created
- [ ] Release notes published
- [ ] HACS metadata updated
- [ ] Community notified (Discord, forum)
- [ ] Monitor GitHub issues for reports
- [ ] Watch system health metrics

### Monthly

- [ ] Review incident logs
- [ ] Update this runbook
- [ ] Test rollback procedure
- [ ] Test hotfix procedure
- [ ] Security audit

---

## Escalation Path

```
User Reports Issue
        ↓
Developer triages (P0/P1/P2/P3)
        ↓
    P0/P1? → Immediate action
    P2? → Add to roadmap
    P3? → Community can help
        ↓
Fix ready → Test locally + remote HA
        ↓
Release hotfix (P0) or next release (P1/P2)
        ↓
Post-Incident Review (P0 only)
        ↓
Update documentation
```

---

## Contact

**Security Issues:** Don't open public issue **Report:** GitHub Security
Advisory (private) **Response Time:** <48 hours acknowledgment

**General Issues:** GitHub Issues tracker **Feature Requests:** GitHub
Discussions **HA Community:** HA Forums

---

## References

- [HA Integration Quality Checklist](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [SLA Best Practices](https://www.atlassian.com/incident-management/handbook/slas)
- [Post-Incident Reviews](https://www.atlassian.com/incident-management/handbook/postmortems)
