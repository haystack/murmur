MAILING_LIST = '';


/* on form submission event e, send an email to MAILING_LIST */
function sendEmail(e) {

  // put all the data from the form into an array
  var formSubmission = e.response.getItemResponses();
  var formData = [];
  formSubmission.forEach(function(d){
    data = d.getResponse();
    formData.push(data);
  });

  // generate email versions with data 
  var email = generateEmails(formData);
  
  // send message 
  MailApp.sendEmail({
    to: MAILING_LIST,
    subject: 'New publication: ' + formData[1],
    htmlBody: email.HTML,
    body: email.plain
  });

  // send confirmation email
  var submitterEmail = formData[0];
  var pubName = formData[1];
  var editLink = e.response.getEditResponseUrl();

  var confEmailPlain = 'Your publication "' + pubName + '" has been successfully submitted.\n'; 
  confEmailPlain += 'To edit your submission, visit the following URL: ' + editLink; 

  var confEmailHTML = 'Your publication "' + pubName + '" has been successfully submitted.<br>';
  confEmailHTML += 'To edit your submission, visit <a href="' + editLink + '">this link.</a>'; 

  MailApp.sendEmail({
    to: submitterEmail,
    subject: 'Publication submitted',
    htmlBody: confEmailHTML,
    body: confEmailPlain
  });
}

/* given a string in the form LastName, FirstName [Mid. Init.], 
convert it to standard name format for ACM citations. */
function formatAuthor(authString) {
  var names = authString.split(',');
  var firstName = names[1].trim();
  var firstSplit = firstName.split(' ');
  if (firstSplit.length == 1) {
    return names[0] + ', ' + firstName[0] + '.';
  } 
  var res = names[0] + ', ' + firstSplit[0][0] + '.' + firstSplit.slice(1).join('');
  if (!(res.endsWith('.'))) res += '.';
  return res;
}

/* given an array containing one or more author names, each in the format 
required by formatAuthor, convert them to correct format and then (if more
 han one name) join them together. */
function formatAuthorList(authors) {
  var auths = [];
  authors.forEach(function(a){
    auths.push(formatAuthor(a));
  });
  if (auths.length == 1) return auths[0];

  var s = auths.slice(0, auths.length - 1).join(', ');
  s += ', and ' + auths[auths.length-1];
  return s;
}

/* generate ACM format citation for a journal article. */
function generateACMjournal(authors, year, title, journal, volume, issue, pages, plain) {
  var res = formatAuthorList(authors) + ' ' + year + '. ' + title + '. ';
  if (!(plain)) res += '<i>';
  res += journal;
  if (!(plain)) res += '</i>';
  if (volume.length > 0) res += ', ' + volume;
  if (issue.length > 0) res += ' (' + issue + ')';
  if (pages.length > 0) res += ', ' + pages;
  return res + '.';
}

/* generate ACM format citation for a conference paper. */
function generateACMconfpaper(authors, year, title, proceedings, confPlace, confDate, procCity, procPub, pages, plain) {
  var res = formatAuthorList(authors) + ' ' + year + '. ' + title + '. ';
  if (plain) res += 'In ' + proceedings;
  else res += 'In <i>' + proceedings + '</i>';
  if (confPlace.length > 0) res += ', ' + confPlace;
  if (confDate.length > 0) res += ', ' + confDate;
  if (procPub.length > 0) res += ', ' + procPub;
  if (procCity.length > 0) res += ', ' + procCity;
  if (pages.length > 0) res += ', ' + pages;
  return res + '.';
}

/* generate an ACM-ish citation for any other type of publication. */
function generateOther(authors, year, title, venue, pages, plain) {
  var res = formatAuthorList(authors) + ' ' + year + '. ' + title + '. ';
  if (plain) res += venue;
  else res += '<i>' + venue + '</i>';
  if (pages.length > 0) res += ', ' + pages;
  return res + '.';
}

var cats = {
  'Artificial Intelligence' : 'AI',
  'Communications' : 'comm',
  'Computational Biology' : 'comp_bio',
  'Architecture' : 'architecture',
  'Graphics and Vision' : 'graphics_vision',
  'Networks' : 'networks',
  'Control and Decision Systems' : 'control_decision_sys',
  'Human-Computer Interaction' : 'HCI',
  'Inference' : 'inference',
  'Machine Learning' : 'ML',
  'Natural Language and Speech Processing' : 'NLP_speech',
  'Programming Languages' : 'languages',
  'Software Engineering and Design' : 'sw_eng_design',
  'Robotics' : 'robotics',
  'Signal Processing' : 'signal_processing',
  'Systems' : 'systems',
  'Theory' : 'theory',
  'Operating Systems' : 'OS',
  'Databases' : 'DB',
  'Security' : 'security', 

}

/* generate plainText and HTML emails using data from publications form. */ 
function generateEmails(formData) {
  var submitterEmail = formData[0],
    title = formData[1],
    authors = formData[2],
    pdfURL = formData[3],
    pubLink = formData[4],
    group = formData[5],
    abstract = formData[6],
    plainEnglish = formData[7],
    year = formData[8],
    type = formData[9],
    proceedings,
    confPlace,
    confDate,
    pubCity,
    proceedingsPublisher,
    journal,
    pages,
    volume,
    issue,
    venue,
    categories,
    other,
    keywords;

  if (type == 'Conference publication') {
    proceedings = formData[10];
    confPlace = formData[11];
    confDate = formData[12];
    pubCity = formData[13];
    proceedingsPublisher = formData[14];
    pages = formData[15];
    categories = formData[16];
    other = formData[17];
    keywords = formData[18];
  } else if (type == 'Journal article') {
    journal = formData[10];
    volume = formData[11];
    issue = formData[12];
    pages = formData[13];
    categories = formData[14];
    other = formData[15];
    keywords = formData[16];
  } else {
    venue = formData[10];
    pages = formData[11];
    categories = formdata[12];
    other = formData[13];
    keywords = formData[14];
  }

  var HTML = '<b>Paper submitted by</b>: ' + submitterEmail + '<br><br>';
  var plain = ['Paper submitted by: ' + submitterEmail];
  if (group.length > 0) {
    HTML += '<b>CSAIL Group</b>: ' + group + '<br>';
    plain.push('CSAIL Group: ' + group); 
  }
  
  HTML += '<b>Categories</b>: ' + categories.join(', ') + '<br><br>';
  plain.push('Categories: ' + categories.join(', '));

  var authorList = [];
  authors.split('\n').forEach(function(a){
    authorList.push(a.trim());
  });

  if (type == 'Conference publication') {
    HTML += generateACMconfpaper(authorList, year, title, proceedings, confPlace, confDate, pubCity, proceedingsPublisher, pages, false);
    plain.push('\n' + generateACMconfpaper(authorList, year, title, proceedings, confPlace, confDate, pubCity, proceedingsPublisher, pages, true));
  } else if (type == 'Journal article') {
    HTML += generateACMjournal(authorList, year, title, journal, volume, issue, pages, false);
    plain.push('\n' + generateACMjournal(authorList, year, title, journal, volume, issue, pages, true));
  } else {
    HTML += generateOther(authorList, year, title, venue, pages, false);
    plain.push('\n' + generateOther(authorList, year, title, venue, pages, true));
  }

  HTML  += "<br><br><a href='" + pdfURL + "'>PDF link</a>, ";
  plain.push('\n' + 'PDF link: <' + pdfURL + '>');

  HTML += "<a href='" + pubLink + "'>Publication link</a><br><br>";
  plain.push('Publication link: <' +  pubLink + '>\n');

  if (keywords.length > 0) {
    HTML += '<b>Keywords</b>: ' + keywords + '<br><br>';
    plain.push('Keywords: ' + keywords + '\n');
  }

  HTML += '<b>Abstract</b>: ' + abstract + '<br>';
  plain.push('Abstract: ' + abstract);

  if (plainEnglish.length > 0) {
    HTML += '<b>In plain English</b>: ' + plainEnglish + '<br>';
    plain.push('In plain English: ' + plainEnglish);
  }

  if (other.length > 0) {
    HTML += '<br><b>Other info</b>: ' + other;
    plain.push('\nOther info: ' + other);
  }
  
  var tag_line = '';
  categories.forEach(function(c){
    tag_line += '#' + cats[c] + ' ';
  });
  
  HTML += '<br>' + tag_line + '<br>';
  plain.push('\n' + tag_line);

  return {
    'HTML' : HTML,
    'plain' : plain.join('\n')
  }
}
