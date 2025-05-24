# Getting Your Vercel Token

This guide will help you get the Vercel token needed for GitHub Actions deployment.

## Step 1: Log in to Vercel

Go to [vercel.com](https://vercel.com/dashboard) and log in to your account.

## Step 2: Access your settings

Click on your profile picture in the top-right corner of the dashboard and select "Settings".

## Step 3: Navigate to Tokens section

In the left sidebar of the Settings page, click on "Tokens".

## Step 4: Create a new token

1. Click the "Create" button to generate a new token
2. Give your token a descriptive name like "GitHub Actions Deployment"
3. Choose an appropriate expiration date (or select "No expiration" if you want it to be permanent)
4. Click "Create Token"

## Step 5: Copy your token

Copy the token that appears on your screen. **This is your only chance to copy the token!** If you lose it, you'll need to create a new one.

## Step 6: Add the token to GitHub Secrets

1. Go to your GitHub repository
2. Click on "Settings"
3. In the left sidebar, click on "Secrets and variables" > "Actions"
4. Click "New repository secret"
5. Name: `VERCEL_TOKEN`
6. Value: Paste the token you copied
7. Click "Add secret"

That's it! Your GitHub Actions workflow will now be able to deploy to Vercel using just this token.
