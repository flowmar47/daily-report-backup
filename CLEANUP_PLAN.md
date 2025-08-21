# OhmsAlertsReports Codebase Cleanup and Improvement Plan

## Current Status Summary

### ✅ **Fixed Issues**
1. **RealOnlyMyMamaScraper method error** - Resolved import and method availability
2. **Messenger import errors** - Fixed with fallback mechanisms
3. **Systemd service failures** - Service now running successfully
4. **Scheduling system** - Working with proper error handling

### 🔧 **Current Working Components**
- Daily financial report automation (6:00 AM PST weekdays)
- MyMama scraper with session persistence
- Telegram and Signal messaging (with fallbacks)
- Heatmap generation and distribution
- Systemd service management
- Error handling and retry mechanisms

## Phase 2: Codebase Structure Improvement

### **Problem Areas Identified**

#### 1. **Duplicate and Conflicting Files**
```
❌ Multiple messenger implementations:
- daily-report/messengers/telegram_messenger.py
- daily-report/messengers/signal_messenger.py  
- daily-report/messengers/enhanced_telegram_messenger.py
- daily-report/src/notifiers/telegram_service.py
- daily-report/src/notifiers/signal_service.py
- daily-report/src/messengers/unified_messenger.py

❌ Multiple scraper implementations:
- daily-report/real_only_mymama_scraper.py
- daily-report/enhanced_browserbase_scraper.py
- daily-report/scrapers/mymama_scraper.py
- daily-report/src/scrapers/mymama_scraper.py

❌ Multiple main entry points:
- daily-report/main.py
- daily-report/enhanced_main.py
- daily-report/main_structured.py
- daily-report/service_runner.py
```

#### 2. **Confusing Directory Structure**
```
❌ Overlapping directories:
- daily-report/src/ (new structure)
- daily-report/messengers/ (old structure)
- daily-report/scrapers/ (old structure)
- daily-report/utils/ (old structure)
- src/ (root level)
- utils/ (root level)
```

#### 3. **Configuration Management Issues**
```
❌ Multiple config files:
- daily-report/config.json
- daily-report/configs/master_config.json
- config.json (root)
- configs/consolidated_requirements.txt
```

### **Proposed Cleanup Strategy**

#### **Step 1: Consolidate Messenger System**
```
✅ Keep: daily-report/src/messengers/unified_messenger.py (primary)
✅ Keep: daily-report/messenger_compatibility.py (backwards compatibility)
❌ Remove: All other messenger implementations
```

#### **Step 2: Consolidate Scraper System**
```
✅ Keep: daily-report/real_only_mymama_scraper.py (primary)
✅ Keep: daily-report/enhanced_browserbase_scraper.py (enhanced version)
❌ Remove: All other scraper implementations
```

#### **Step 3: Consolidate Main Entry Points**
```
✅ Keep: daily-report/main.py (primary service entry)
✅ Keep: daily-report/service_runner.py (service management)
❌ Remove: All other main files
```

#### **Step 4: Clean Directory Structure**
```
✅ Keep: daily-report/src/ (new unified structure)
✅ Keep: daily-report/utils/ (local utilities)
❌ Remove: Redundant directories
```

#### **Step 5: Consolidate Configuration**
```
✅ Keep: daily-report/config.json (primary config)
✅ Keep: daily-report/.env (environment variables)
❌ Remove: All other config files
```

## Phase 3: Implementation Plan

### **Week 1: Messenger System Cleanup**
1. Test unified messenger system thoroughly
2. Remove deprecated messenger implementations
3. Update all imports to use unified system
4. Verify backwards compatibility works

### **Week 2: Scraper System Cleanup**
1. Test both scraper implementations
2. Remove deprecated scraper files
3. Update all imports to use primary scrapers
4. Verify data collection works

### **Week 3: Directory Structure Cleanup**
1. Move all files to unified structure
2. Remove redundant directories
3. Update all import paths
4. Verify system functionality

### **Week 4: Configuration Cleanup**
1. Consolidate all configuration files
2. Remove redundant configs
3. Update all config references
4. Verify system configuration

## Phase 4: Testing and Validation

### **Automated Testing**
1. Create comprehensive test suite
2. Test all messaging platforms
3. Test all scraper functionality
4. Test scheduling and automation

### **Manual Testing**
1. Test daily report generation
2. Test message delivery to both platforms
3. Test error handling and recovery
4. Test service restart capabilities

## Phase 5: Documentation and Monitoring

### **Documentation Updates**
1. Update README with new structure
2. Create deployment guide
3. Create troubleshooting guide
4. Document API interfaces

### **Monitoring Improvements**
1. Enhanced logging system
2. Health check endpoints
3. Performance monitoring
4. Alert system for failures

## Success Metrics

### **Code Quality**
- [ ] Reduce codebase size by 40%
- [ ] Eliminate all duplicate implementations
- [ ] Achieve 90%+ test coverage
- [ ] Zero import errors

### **System Reliability**
- [ ] 99.9% uptime for messaging system
- [ ] <5 minute recovery time from failures
- [ ] Zero missed scheduled reports
- [ ] All messages delivered successfully

### **Maintainability**
- [ ] Single source of truth for each component
- [ ] Clear documentation for all interfaces
- [ ] Automated deployment process
- [ ] Easy troubleshooting procedures

## Risk Mitigation

### **Backup Strategy**
1. Create full backup before each phase
2. Maintain rollback capability
3. Test changes in staging environment
4. Gradual rollout with monitoring

### **Fallback Plans**
1. Keep old system running during transition
2. Maintain compatibility layers
3. Quick rollback procedures
4. Emergency contact procedures

## Timeline

- **Week 1-2**: Messenger and scraper cleanup
- **Week 3-4**: Directory structure cleanup  
- **Week 5-6**: Configuration and testing
- **Week 7-8**: Documentation and monitoring
- **Week 9**: Final validation and deployment

## Next Steps

1. **Immediate**: Start with messenger system cleanup
2. **Short-term**: Complete scraper consolidation
3. **Medium-term**: Restructure directories
4. **Long-term**: Implement monitoring and documentation

---

*This plan will be updated as implementation progresses and new issues are discovered.* 