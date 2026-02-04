```md
# TODO

## Milestone 1 — Working MVP
- [ ] Backend API runs and returns mock schedule
- [ ] Web client fetches /schedules/today and renders it
- [ ] Desktop client fetches /schedules/today and shows it

## Milestone 2 — Persistence
- [ ] Add SQLite tables for tasks and feedback
- [ ] Implement create/list tasks using DB
- [ ] Store feedback in DB

## Milestone 3 — Rule-based Scheduler
- [ ] Use tasks + appointments to build schedule
- [ ] Enforce constraints (no overlaps, max hours)
- [ ] Add priority engine (deadlines + importance)

## Milestone 4 — ML Enhancements
- [ ] Stress prediction model (supervised)
- [ ] Q-learning policy for schedule adjustments
- [ ] Train/update based on feedback logs

## Immediate

Add CORS so browser fetch works cleanly

Implement DB storage for tasks

Replace mock schedule route with rule_based scheduler call

Log feedback into DB

Add ML later after you have real usage data
