# Sending Emails via Google Forms Submission

The code in its current state does as follows:
1) Parse a response to a Google Form, which collects information about new publications by members of our lab
2) Generate HTML and plaintext for an email containing that info
3) Post the message to a Murmur group

You can see what our form looks like [here]() (TODO: put a link to a copy of the form here.) 

Instructions for using with your own forms:
1) Create a Google Form with your desired questions/form fields.
2) In the form editing interface, click the three vertical dots in the top right, and then "<> Script Editor..." in the dropdown. 
3) Write a Javascript function ```yourFunctionName``` that takes in a single parameter, an [event object](https://developers.google.com/apps-script/guides/triggers/events) ```e```. This function will be executed on each form submission. (See our ```sendEmail``` function for an example.)
4) In the top menu in the script editor, click "Resources" and then "Current project's triggers". Add a new trigger that runs ```yourFunctionName``` on form submit. If the function sends emails, clicking "save" will lead to a new window opening that requests permission to send emails as you.
5) Fill out your form and test it out! 

The "Logs" and "Execution transcript" on the script editor (under "View") are both useful for debugging. 