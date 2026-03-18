import os
import re

directories = ["c:/Users/mraee/djangoprojects/calculators/templates/calculators"]
files_to_check = ["reprice_dashboard.html", "clarity_dashboard.html", "drip_dashboard.html", "pdf_report.html", "pdf_capital_gains.html"]

for d in directories:
    for filename in files_to_check:
        filepath = os.path.join(d, filename)
        if not os.path.exists(filepath): continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove '$' inside HTML labels: "Price ($)" -> "Price" and "Investment ($)" -> "Investment"
        content = content.replace(' ($)', '')
        content = content.replace(' ($/£)', '')
        
        # Remove '$' from HTML text nodes like >$0.00< or >$-<
        content = re.sub(r'>\$([0-9.\-]+)<', r'>\1<', content)
        
        # Remove '$' from JS template strings: $${data.var} -> ${data.var}
        # Note that standard JS template interpolation is ${VAR}, so $${VAR} was literally rendering $ in front. 
        # By replacing $${ with ${ we remove the currency symbol but keep the injection.
        content = content.replace('$${', '${')
        
        # Handle string concatenations like: '$' + ...
        content = content.replace("'$' + ", "'' + ")
        
        # Handle literal $ in JS template tags like: `Target $${parseFloat...` -> already handled by $${ -> ${
        # But wait, what if it was: `Buy $${...}`? It's handled.
        # What about `Target $${...}`?
        
        # Handle PDF templates where we had ${{ variable }} -> {{ variable }}
        content = content.replace('${{', '{{')
        
        # Any specific edge cases like `$-` inside tags
        content = content.replace('>$-<', '>-<')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print("Currency replacement complete")
