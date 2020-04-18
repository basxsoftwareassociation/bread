function tableToExcel(downloadelement, tableelement, worksheetname, filename) {
    // e.g. <input type="button" onclick="tableToExcel(this, tableelement, 'mysheet', 'myfile.xls')" value="Export to Excel">
    var uri = 'data:application/vnd.ms-excel;base64,'
    var template = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><meta charset="utf-8"/><head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>{worksheet}</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body><table>{table}</table></body></html>'
    var base64 = function (s) { return window.btoa(unescape(encodeURIComponent(s))) }
    var format = function (s, c) { return s.replace(/{(\w+)}/g, function (m, p) { return c[p]; }) }
    var ctx = { worksheet: worksheetname || 'Worksheet', table: table.innerHTML }

    downloadelement.href = uri + base64(format(template, ctx));
    downloadelement.download = filename;
    downloadelement.click();
}
