const fs = require('fs');
const path = require('path');

try {
  const orgId = process.env.VERCEL_ORG_ID || process.env.NEXT_PUBLIC_VERCEL_ORG_ID || 'team_dummy_org_id_12345678';
  const projectId = process.env.VERCEL_PROJECT_ID || process.env.NEXT_PUBLIC_VERCEL_PROJECT_ID || 'prj_dummy_project_id_12345678';

  const vercelDir = path.join(__dirname, '.vercel');
  if (!fs.existsSync(vercelDir)) {
    fs.mkdirSync(vercelDir, { recursive: true });
  }
  
  const projectConfig = {
    orgId,
    projectId,
    projectName: 'vervetech'
  };

  fs.writeFileSync(
    path.join(vercelDir, 'project.json'),
    JSON.stringify(projectConfig, null, 2)
  );
  console.log('Successfully linked Vercel project via .vercel/project.json with orgId: ' + orgId);
} catch (error) {
  console.error('Error setting up Vercel project link:', error);
}
