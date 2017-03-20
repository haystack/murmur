// store the edit link for the form in the spreadsheet 
function storeEditURL(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Form Responses 1');
  var urlCol = 28;
  var row = Math.floor(sheet.getLastRow());
  var resIndex = row - 2;
  var form = FormApp.openByUrl('');
  var editLink = form.getResponses()[resIndex].getEditResponseUrl();
  sheet.getRange(row, urlCol).setValue([editLink]);
}