const fs = require('fs');
const path = require('path');

try {
  const vercelDir = path.join(process.cwd(), '.vercel');
  if (!fs.existsSync(vercelDir)) {
    fs.mkdirSync(vercelDir, { recursive: true });
  }

  const projectId = process.env.VERCEL_PROJECT_ID || process.env.NEXT_PUBLIC_VERCEL_PROJECT_ID || 'dummy_project_id';
  const orgId = process.env.VERCEL_ORG_ID || process.env.NEXT_PUBLIC_VERCEL_ORG_ID || 'dummy_org_id';

  const projectJson = {
    projectId,
    orgId
  };

  fs.writeFileSync(path.join(vercelDir, 'project.json'), JSON.stringify(projectJson, null, 2));
  console.log('Successfully generated .vercel/project.json');
} catch (error) {
  console.error('Error generating .vercel/project.json:', error);
}