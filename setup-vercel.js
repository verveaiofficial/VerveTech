const fs = require('fs');
const path = require('path');

try {
  const orgId = process.env.VERCEL_ORG_ID || process.env.NEXT_PUBLIC_VERCEL_ORG_ID;
  const projectId = process.env.VERCEL_PROJECT_ID || process.env.NEXT_PUBLIC_VERCEL_PROJECT_ID;

  if (orgId && projectId) {
    const vercelDir = path.join(__dirname, '.vercel');
    if (!fs.existsSync(vercelDir)) {
      fs.mkdirSync(vercelDir, { recursive: true });
    }
    fs.writeFileSync(
      path.join(vercelDir, 'project.json'),
      JSON.stringify({ orgId, projectId }, null, 2)
    );
    console.log('Successfully linked Vercel project via .vercel/project.json');
  } else {
    console.warn('Warning: VERCEL_ORG_ID or VERCEL_PROJECT_ID env variables are not set.');
  }
} catch (error) {
  console.error('Error setting up Vercel project link:', error);
}