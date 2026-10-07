// Parse every PDF in ./inbox and write JSON next to it. Mind 30 requests per 60 seconds per IP.
const fs = require('fs');
const path = require('path');
const ResumeReader = require('../node');

const rr = new ResumeReader(process.env.RESUME_KEY);
(async () => {
  for (const f of fs.readdirSync('inbox').filter((n) => n.endsWith('.pdf'))) {
    try {
      const { resume } = await rr.parseFile(path.join('inbox', f));
      fs.writeFileSync(path.join('inbox', f + '.json'), JSON.stringify(resume, null, 2));
      await new Promise((r) => setTimeout(r, 2100));
    } catch (e) {
      console.error(f, e.message);
    }
  }
})();
