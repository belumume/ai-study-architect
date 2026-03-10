# Critical Notes - DO NOT LOSE

## 🔴 CRITICAL - Never Change These
1. **BACKUP_ENCRYPTION_KEY** - If you lose or change this, ALL previous backups become unrecoverable
   - Currently stored in Proton Pass
   - Used for Fernet encryption (AES-128-CBC + HMAC)
   
2. **Pre-Deploy Command in Render** - MUST remain empty
   - Any migration command will fail due to pre-existing tables
   - Migrations are handled in start_render.sh

## 🟡 Important Fixes Applied

### FAB Badge Issue (2025-08-24)
- **Problem**: Badge was counting to 99 during streaming (incrementing per chunk)
- **Fix**: Only increment once on first chunk when `assistantMessage.content === ''`
- **File**: `frontend/src/components/chat/ChatInterface.tsx` line 287

### Double Scrollbar Issue (2025-08-24)
- **Problem**: Study Materials panel had two scrollbars (outer Paper + inner List)
- **Fix**: Removed `overflow: 'auto'` from Paper, used flexbox layout
- **Files**: `App.tsx` line 283, `ContentSelector.tsx` line 129

### Streaming Empty Responses (2025-08-23)
- **Problem**: API keys checked at import time before env vars loaded
- **Fix**: Use `@property` decorator for runtime checking
- **Files**: `claude_service.py`, `openai_fallback.py`

## 🟢 Quick Fixes for Common Issues

```bash
# If chat is blank/empty
1. Check API keys are set in Render env vars
2. Verify @property decorators in place
3. Check credentials: 'omit' in ChatInterface.tsx

# If build fails on Render
1. Ensure Pre-Deploy is EMPTY
2. Check build_starter.sh has Unix line endings
3. Verify requirements.txt is complete

# If PostgreSQL won't connect locally (Windows)
Use port 5433, not 5432

# If backup fails
Check BACKUP_TOKEN matches between GitHub and Render
```

## 🔵 Testing Credentials
- **Username**: dropout_taekwondo
- **Password**: (in your password manager)
- **Test on**: https://aistudyarchitect.com

## 🟣 Architecture Decisions That Matter

1. **Why Claude Primary, OpenAI Fallback?**
   - Claude: 93.7% on HumanEval (better for education)
   - OpenAI: 92.0% (good fallback)
   - Socratic questioning works better with Claude

2. **Why No Redis?**
   - MockRedisClient works fine for current scale
   - Saves $0-20/month
   - Can add Upstash later if needed

3. **Why 7 Agents?**
   - Each has specific role in learning process
   - Not arbitrary - designed for cognitive development
   - Lead Tutor orchestrates the others

## 🔶 Deployment Checklist

```bash
# Every deployment
git add . && git commit -m "type: message" && git push

# Vercel deploys immediately
# Render takes 2-3 minutes

# Verify deployment
curl https://ai-study-architect.onrender.com/api/v1/health
```

## 🔷 Environment Variables Priority

**MUST HAVE**:
- ANTHROPIC_API_KEY
- OPENAI_API_KEY  
- DATABASE_URL (auto-set by Render)
- BACKUP_ENCRYPTION_KEY (NEVER CHANGE)

**NICE TO HAVE**:
- R2/S3 backup credentials
- BACKUP_TOKEN

**AUTO-GENERATED** (don't set manually):
- SECRET_KEY
- JWT_SECRET_KEY

## 📝 For Your CS50 Submission

1. **Add video URL to README.md** line 2
2. **Version tagged**: v1.0.0
3. **Live site**: https://aistudyarchitect.com
4. **GitHub**: https://github.com/belumume/ai-study-architect

## 🚨 If Something Breaks

1. **Check Render logs first** - usually shows the issue
2. **Frontend issues** - Check Vercel function logs
3. **Can't fix it?** - Rollback in Render/Vercel dashboard
4. **Still broken?** - Restore from R2/S3 backup

## 💡 Future Improvements to Consider

1. **Add Ollama** for local/private AI option
2. **Implement WebSockets** for better real-time feel
3. **Add voice input/output** for accessibility
4. **Create mobile app** with React Native
5. **Add collaborative study** features

## 🔐 Security Reminders

- Rotate API keys quarterly (set calendar reminder)
- Test backup restore monthly
- Never commit secrets to git
- Keep BACKUP_ENCRYPTION_KEY safe
- Use different passwords for dev/prod

---

**Last Updated**: 2025-08-24
**Next Review**: Before any major changes
**Contact**: Check GitHub issues if you forget something