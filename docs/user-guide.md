# User Guide

## Getting Started

Welcome to the Personal Analytics Dashboard! This guide will help you get started with creating optimized daily schedules.

## First Time Setup

1. **Install Dependencies**: Follow the installation instructions in the main README.md
2. **Start the System**: Use the quick start scripts or run components separately
3. **Seed Sample Data** (Development): Run the admin seed script to create test data
4. **Create Account**: Register a new user account or use the seeded admin account
5. **Enable 2FA**: For security, enable two-factor authentication in settings

### Seeding Sample Data

For development and testing, you can populate the database with sample data:

```bash
python scripts/seed_admin.py
```

This creates an admin user (`admin@admin.com` / `Test1234`) and two weeks of sample tasks. Run this after the backend is running for the first time.

## Using the Application

### Dashboard Overview

The main dashboard shows your schedule for today and upcoming days. Key elements:

- **Today's Schedule**: Time-blocked view of your tasks
- **Task List**: All pending and completed tasks
- **Quick Actions**: Add new tasks, provide feedback
- **Analytics**: View your scheduling patterns and preferences

### Managing Tasks

#### Creating Tasks
1. Click "Add Task" button
2. Enter task details:
   - Title and description
   - Due date and time
   - Estimated duration
   - Importance level (Low/Medium/High)
   - Category (Work/Personal/Health)
3. Save the task

#### Editing Tasks
- Click on any task in the list or schedule view
- Modify details as needed
- Changes will automatically update your schedule

#### Completing Tasks
- Mark tasks as complete when finished
- The system learns from your completion patterns

### Schedule Management

#### Viewing Your Schedule
- **Daily View**: Today's schedule with time blocks
- **Weekly View**: Overview of the upcoming week
- **Calendar View**: Month overview with task indicators

#### Providing Feedback
After each day, rate your schedule:
- **Balanced**: Schedule was just right
- **Stressed**: Too many tasks or poor timing
- **Underwhelmed**: Not enough tasks or too easy

This feedback helps the system optimize future schedules.

### Settings and Preferences

#### Profile Settings
- Update personal information
- Change password
- Manage notification preferences

#### Security Settings
- Enable/Disable 2FA
- View login history
- Manage trusted devices

#### Scheduling Preferences
- Set preferred work hours
- Configure break preferences
- Adjust task prioritization rules

### Analytics and Insights

View insights about your productivity:
- **Completion Rates**: Task completion statistics
- **Time Distribution**: How you spend your time
- **Stress Patterns**: When you're most/least stressed
- **Optimization Trends**: How your schedules have improved

## Using Different Clients

### Web Client
- Access via browser at `http://localhost:5173`
- Full-featured interface
- Works on any device with a browser

### Desktop App (Tauri)
- Native application window
- Better performance
- System integration features

### Python Desktop Client
- Lightweight native app
- Minimal resource usage
- Good for low-power devices

## Troubleshooting

### Common Issues

**Can't connect to backend**
- Ensure the backend server is running (`uvicorn backend.app:app --reload`)
- Check that the API is accessible at `http://127.0.0.1:8000`

**Schedule not updating**
- Refresh the page
- Check browser console for errors
- Ensure you have internet connectivity

**Tasks not saving**
- Verify you're logged in
- Check form validation errors
- Ensure database is accessible

**ML features not working**
- ML components may be disabled in settings
- Check that models are trained (admin feature)

### Getting Help

- Check the API documentation at `http://127.0.0.1:8000/docs`
- Review the setup instructions in SETUP.md
- Check the TODO.md for known issues and planned features

## Advanced Features

### Custom Scheduling Rules
- Set recurring tasks
- Define time blocks (e.g., "No work after 6 PM")
- Priority overrides for urgent tasks

### Integration Features
- Import tasks from external calendars
- Export schedules to calendar apps
- API access for third-party integrations

### Admin Features (Admin Users Only)
- User management
- System analytics
- Model training and updates
- Database maintenance

## Best Practices

1. **Regular Feedback**: Rate your schedules daily for better optimization
2. **Complete Tasks**: Mark tasks as done to help the system learn
3. **Update Preferences**: Keep your scheduling preferences current
4. **Review Analytics**: Use insights to improve your productivity habits

## Privacy and Security

- All data is encrypted in transit and at rest
- User feedback is anonymized for ML training
- You can request data deletion at any time
- 2FA is recommended for account security