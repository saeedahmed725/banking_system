# Vercel Deployment Guide for Banking System

This guide will help you deploy your Banking System application to Vercel using GitHub Actions.

## Prerequisites

1. A GitHub repository with your Banking System code
2. A Vercel account - Sign up at [vercel.com](https://vercel.com) if you don't have one
3. The Vercel CLI (optional but recommended) - Install with `npm i -g vercel`

## Step 1: Connect Your Repository to Vercel

### Option 1: Using the Vercel Dashboard (Recommended for first-time setup)

1. Go to the [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" > "Project"
3. Import your repository from GitHub
4. Configure project settings:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: Leave empty (handled by vercel.json)
   - Output Directory: Leave empty
5. Click "Deploy"

### Option 2: Using Vercel CLI

1. Open a terminal in your project directory
2. Run `vercel login` and follow the authentication process
3. Run `vercel` to deploy
4. Follow the prompts to link your project

## Step 2: Get Your Vercel Credentials

Once your project is set up on Vercel, you need to get three important values to use in GitHub Actions:

1. **VERCEL_TOKEN**:
   - Go to your Vercel dashboard
   - Click on your avatar in the top-right corner and select "Settings"
   - Go to "Tokens"
   - Create a new token with a description like "GitHub Actions"
   - Copy the token value

2. **VERCEL_ORG_ID** and **VERCEL_PROJECT_ID**:
   - If you used Vercel CLI and ran `vercel link`, check the `.vercel/project.json` file
   - OR run `vercel project ls` to list your projects and find the project ID
   - For the org ID, you can find it in your account settings

## Step 3: Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Click "Settings" > "Secrets and variables" > "Actions"
3. Add the following repository secrets:
   - Name: `VERCEL_TOKEN`, Value: (your token from step 2)
   - Name: `VERCEL_ORG_ID`, Value: (your org ID from step 2)
   - Name: `VERCEL_PROJECT_ID`, Value: (your project ID from step 2)

## Step 4: Configuring Environment Variables

If your application requires specific environment variables:

1. Go to your project on Vercel dashboard
2. Click "Settings" > "Environment Variables"
3. Add any required variables (e.g., database connection strings)

## Understanding the Deployment Configuration

### vercel.json

This file tells Vercel how to deploy your application:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "web/app.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "15mb" }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "web/app.py"
    }
  ]
}
```

### GitHub Actions Workflow

The workflow file `.github/workflows/banking-app-workflow.yml` does the following:

1. Runs tests on every push and pull request
2. Deploys to Vercel when tests pass and changes are pushed to main/master

## Troubleshooting

### Deployment Issues

- **Error: No Output Directory**: Check your `vercel.json` configuration.
- **Timeout during build**: Your build might be too complex for Vercel's free tier limits.
- **Database connection issues**: Ensure you're using environment variables for database connections.

### GitHub Actions Issues

- **Missing secrets**: Make sure all three Vercel secrets are added to your repository.
- **Test failures**: Fix any failing tests before deployment can proceed.

## Database Considerations

For a production deployment, consider:

1. Using a cloud database service instead of SQLite
2. Configuring database migrations
3. Setting up proper environment variables for database credentials

## Monitoring Your Deployment

After deployment:
1. Visit your project URL (usually `https://your-project-name.vercel.app`)
2. Check Vercel's deployment logs for any issues
3. Monitor application performance in the Vercel dashboard

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Flask on Vercel Guide](https://vercel.com/guides/deploying-flask-with-vercel)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
