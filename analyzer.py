import os
import sys

# Use home-relative path for portability
brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
hackops_convs = []

if not os.path.exists(brain_dir):
    print(f"Error: Brain directory not found at {brain_dir}")
    sys.exit(1)

for conv in os.listdir(brain_dir):
    p = os.path.join(brain_dir, conv, '.system_generated', 'logs', 'overview.txt')
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                t = f.read()
                if 'hackops-project' in t.lower() or 'hackops' in t.lower():
                    lines = t.split('\n')
                    user_msg = []
                    for i, l in enumerate(lines):
                        if '<USER_REQUEST>' in l:
                            user_msg = lines[i+1:i+6]
                            break
                        elif 'User:' in l and not user_msg:
                            user_msg = lines[i:i+4]
                            break
                        elif 'user objective:' in l.lower():
                            user_msg = lines[i:i+2]
                            break
                    hackops_convs.append(f'- **Conversation {conv}**: {user_msg}')
        except Exception as e:
            pass

with open('conv_history2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(hackops_convs))
print(f"Processed {len(hackops_convs)} conversations.")
