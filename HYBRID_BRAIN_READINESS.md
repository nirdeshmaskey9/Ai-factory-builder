# 🧠 Hybrid Brain Readiness Checklist - v3.7.0

**Phase:** v3.7.0-hybrid-brain-initialization  
**Target:** JoJo Hybrid Integration Preparation  
**Hardware:** Alienware m18 R2 (8GB VRAM / 32GB RAM)

---

## ✅ Pre-Integration Checklist

### 1. Local Trio Configuration
- [x] **Model Definitions Updated**
  - [x] `src/ai_factory/advisor/local_trio.py` - Models assigned
  - [x] `src/ai_factory/model_registry.json` - Registry updated
  - [x] Version bumped to v3.7.0

- [ ] **Models Installed**
  - [ ] Qwen 2 1.5B Instruct Q4 pulled via Ollama
  - [ ] Mistral 7B Instruct v0.3 Q4 pulled via Ollama
  - [ ] Phi-3 Mini 4K Instruct Q4 pulled via Ollama
  - [ ] All models verified with `ollama list`

- [ ] **Health Verification**
  - [ ] Strategist model responds to test prompts
  - [ ] Memory model responds to test prompts
  - [ ] Executor model responds to test prompts
  - [ ] Advisor health endpoint returns all healthy
  - [ ] Trio Manager thread monitoring active

### 2. Environment Configuration
- [x] **.env Template Created**
  - [x] Model assignments documented
  - [x] Ollama host configured
  - [x] Cloud fallback settings present

- [ ] **.env File Updated**
  - [ ] `AI_FACTORY_LOCAL_STRATEGIST_MODEL` set
  - [ ] `AI_FACTORY_LOCAL_MEMORY_MODEL` set
  - [ ] `AI_FACTORY_LOCAL_EXECUTION_MODEL` set
  - [ ] `OLLAMA_HOST` verified
  - [ ] `OPENAI_API_KEY` present (for fallback)

### 3. Infrastructure Readiness
- [x] **Setup Scripts**
  - [x] `scripts/setup_ollama.ps1` - Windows setup
  - [x] `scripts/setup_ollama.sh` - Linux/macOS setup
  - [x] `scripts/validate_trio.ps1` - Health validation

- [ ] **Ollama Daemon**
  - [ ] Ollama installed and running
  - [ ] Accessible at `http://127.0.0.1:11434`
  - [ ] Version compatible with models

### 4. System Integration
- [x] **Code Updates**
  - [x] `local_trio.py` updated with new models
  - [x] `model_registry.json` includes VRAM estimates
  - [x] Version tracking updated

- [ ] **Runtime Validation**
  - [ ] FastAPI app starts without errors
  - [ ] Advisor router accessible at `/advisor/models`
  - [ ] Trio health endpoint returns correct models
  - [ ] Bridge can route to local models
  - [ ] Orchestrator can use local trio

### 5. Performance Baseline
- [ ] **Latency Measurements**
  - [ ] Strategist inference time: _____ ms
  - [ ] Memory inference time: _____ ms
  - [ ] Executor inference time: _____ ms
  - [ ] All within acceptable range (<2000ms)

- [ ] **Resource Usage**
  - [ ] VRAM usage monitored: _____ GB
  - [ ] RAM usage acceptable: _____ GB
  - [ ] CPU utilization reasonable
  - [ ] No memory leaks detected

### 6. Fallback Testing
- [ ] **Cloud Fallback**
  - [ ] Cloud models accessible (GPT-4o)
  - [ ] Fallback triggers when local unavailable
  - [ ] Privacy strict mode respects local-only
  - [ ] Mock mode works when both unavailable

- [ ] **Error Handling**
  - [ ] Graceful degradation on model failure
  - [ ] Health checks recover after restart
  - [ ] Logs capture fallback decisions
  - [ ] UI shows correct status

### 7. Documentation
- [x] **Status Documents**
  - [x] `LOCAL_TRIO_STATUS.md` - Model overview
  - [x] `HYBRID_BRAIN_READINESS.md` - This checklist
  - [x] `.env.template` - Configuration reference

- [ ] **Operational Docs**
  - [ ] Setup instructions verified
  - [ ] Troubleshooting guide updated
  - [ ] Performance benchmarks documented

---

## 🎯 JoJo Integration Prerequisites

### Phase 1: Local Trio Stability (Current)
- [x] Models configured and optimized
- [ ] Models installed and validated
- [ ] Health monitoring active
- [ ] Fallback mechanisms tested

### Phase 2: Bridge Integration (Next)
- [ ] Bridge can route to local trio
- [ ] Persona mode works with local models
- [ ] Hybrid chat (local + cloud) functional
- [ ] Memory integration with local synthesis

### Phase 3: JoJo Persona Linking (Future)
- [ ] Qwen 7B base model for JoJo voice
- [ ] LoRA adapters prepared (Identity, Truth, Tools, Strategy)
- [ ] Persona stabilization with local trio
- [ ] Full hybrid intelligence operational

---

## 🔍 Validation Commands

### Quick Health Check
```powershell
# Windows
.\scripts\validate_trio.ps1

# Or Python
python -c "from ai_factory.advisor.advisor_service import verify_local_health; import json; print(json.dumps(verify_local_health(), indent=2))"
```

### Model List
```bash
ollama list
```

### Test Individual Models
```bash
ollama run qwen2:1.5b-instruct-q4_K_M "Hello, test"
ollama run mistral:7b-instruct-v0.3-q4_K_M "Hello, test"
ollama run phi3:mini-4k-instruct-q4_K_M "Hello, test"
```

### Advisor Endpoint
```bash
curl http://127.0.0.1:8015/advisor/models
curl http://127.0.0.1:8015/advisor/trio_health
```

---

## ⚠️ Known Limitations

1. **VRAM Constraint:** Total 7.5GB usage leaves minimal headroom
   - Solution: Models are Q4 quantized for efficiency
   - Monitor: Watch for OOM errors during heavy usage

2. **Model Size:** Cannot use 13B+ models on 8GB VRAM
   - Current: All models <8B parameters
   - Future: Upgrade GPU or use cloud for larger models

3. **Concurrency:** Limited to 1-2 concurrent requests per model
   - Reason: VRAM sharing
   - Workaround: Sequential processing or cloud fallback

---

## 📊 Success Criteria

### Minimum Viable
- ✅ All three models installed
- ✅ Health checks passing
- ✅ Basic inference working
- ✅ Fallback mechanisms functional

### Production Ready
- [ ] Latency <2000ms for all models
- [ ] 99%+ health check success rate
- [ ] Zero OOM errors in 24h test
- [ ] Bridge integration complete

### JoJo Ready
- [ ] Persona mode with local trio
- [ ] Hybrid chat operational
- [ ] Memory synthesis working
- [ ] Full workflow end-to-end

---

## 🚀 Next Steps

1. **Immediate:**
   - Run `setup_ollama.ps1` to install models
   - Execute `validate_trio.ps1` to verify health
   - Update `.env` with model assignments

2. **Short-term:**
   - Test Bridge integration with local trio
   - Validate Orchestrator workflows
   - Monitor performance and adjust if needed

3. **Long-term:**
   - Prepare JoJo Qwen 7B base model
   - Develop LoRA adapters
   - Integrate persona with local trio

---

## 📝 Notes

- **Hardware Optimization:** Models selected specifically for 8GB VRAM constraint
- **Quantization:** Q4_K_M provides best quality/size balance
- **Future Proofing:** Configuration supports easy model swaps
- **Monitoring:** Trio Manager provides continuous health tracking

---

**Status:** 🟡 Configuration Complete, Awaiting Model Installation  
**Last Updated:** 2025-01-XX  
**Next Review:** After model installation and validation

