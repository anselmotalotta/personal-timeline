# Check Docker Status

## ✅ Good News!

Containers started successfully! The nuclear option worked.

---

## 🔍 Check All Services

Run these commands:

### 1. Check all containers (including stopped ones)
```bash
docker compose ps -a
```

### 2. Check logs for each service

**Backend logs:**
```bash
docker compose logs backend
```

**QA logs:**
```bash
docker compose logs qa
```

**Frontend logs:**
```bash
docker compose logs frontend
```

### 3. Follow live logs
```bash
# All services
docker compose logs -f

# Or specific service
docker compose logs -f qa
```

---

## 📊 Expected Behavior

### Backend
- **Status**: `Exited (0)` - This is NORMAL!
- **Why**: Backend runs once to import data, then exits
- **Check logs**: `docker compose logs backend` should show import completion

### QA API
- **Status**: Should be `Up`
- **Port**: 57485
- **Test**: `curl http://localhost:57485/test`

### Frontend
- **Status**: `Up` ✅ (already confirmed)
- **Port**: 52692
- **Access**: http://localhost:52692

---

## 🚀 Access Your Timeline

Open your browser and go to:

**http://localhost:52692**

You should see the Personal Timeline interface!

---

## 🐛 If QA or Backend Not Showing

### Check if they exited with errors:
```bash
docker compose ps -a
```

Look for exit codes:
- `Exited (0)` = Success
- `Exited (1)` or higher = Error

### View error logs:
```bash
docker compose logs backend | tail -50
docker compose logs qa | tail -50
```

---

## 💡 Common Issues

### Backend shows "Exited (0)"
✅ **This is normal!** Backend runs once and exits. Check logs:
```bash
docker compose logs backend
```

Should show:
```
--------------Data Import Complete--------------
Data Stats by source:::
Source :  Count
FacebookPosts :  X
```

### QA service not running
Check logs for errors:
```bash
docker compose logs qa
```

Common issues:
- Missing dependencies (already fixed in our requirements.txt)
- OpenAI API key missing (optional, not required)
- Database not found (should be auto-created)

### Frontend shows "Exited" instead of "Up"
Check logs:
```bash
docker compose logs frontend
```

Possible causes:
- npm install failed
- Port conflict (we just fixed this)
- Build errors

---

## ✅ Quick Health Check

Run all these commands:

```bash
# Check status
docker compose ps -a

# Test QA API
curl http://localhost:57485/test

# Test Frontend
curl http://localhost:52692

# View all logs
docker compose logs --tail=20
```

---

## 🎯 Next Steps

1. **Check status of all services:**
   ```bash
   docker compose ps -a
   ```

2. **View logs if anything failed:**
   ```bash
   docker compose logs
   ```

3. **Open frontend in browser:**
   ```
   http://localhost:52692
   ```

4. **Verify your data is there:**
   - Timeline should show your Facebook posts
   - Photos should be visible
   - Map view should show locations

---

## 📝 Quick Commands Reference

```bash
# View status
docker compose ps -a

# View logs
docker compose logs -f

# Restart a service
docker compose restart qa

# Stop everything
docker compose down

# Start everything
docker compose up -d

# Rebuild a service
docker compose build qa
docker compose up -d qa

# Check backend import results
docker compose logs backend | grep "Data Stats"
```

---

**Now run this to see the full status:**

```bash
docker compose ps -a
docker compose logs backend | tail -30
```

This will show if backend completed successfully and imported your Facebook data! 🎉
