/**
 * Bu kodni Google Sheets'ning "Extensions" -> "Apps Script" bo'limiga
 * to'liq nusxalab qo'ying (README.md dagi ko'rsatmaga qarang).
 *
 * Ikki jadval avtomatik yaratiladi:
 *   - "Buyurtmalar": har bir tasdiqlangan buyurtma shu yerga yoziladi
 *   - "Mijozlar": har bir mijozning ismi, telefoni va saqlangan manzillari
 *
 * Agar avval eski versiyadagi "Buyurtmalar" jadvalingiz bo'lsa, ustunlar
 * tuzilishi o'zgargani uchun o'sha eski varaqni (sheet tab) o'chirib tashlang —
 * skript uni qaytadan to'g'ri ustunlar bilan yaratib beradi.
 */

function getOrCreateSheet(name, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
  } else if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }
  return sheet;
}

function doPost(e) {
  var data = JSON.parse(e.postData.contents);

  if (data.action === "save_profile") {
    var sheet = getOrCreateSheet("Mijozlar", ["UserID", "Ism", "Telefon", "Manzillar (JSON)", "Yangilangan"]);
    var values = sheet.getDataRange().getValues();
    var rowIndex = -1;
    for (var i = 1; i < values.length; i++) {
      if (String(values[i][0]) === String(data.user_id)) {
        rowIndex = i + 1;
        break;
      }
    }
    var rowData = [
      data.user_id,
      data.name || "",
      data.phone || "",
      JSON.stringify(data.addresses || []),
      new Date()
    ];
    if (rowIndex > 0) {
      sheet.getRange(rowIndex, 1, 1, rowData.length).setValues([rowData]);
    } else {
      sheet.appendRow(rowData);
    }
    return ContentService.createTextOutput(JSON.stringify({ status: "ok" }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Standart holat: yangi buyurtmani "Buyurtmalar" jadvaliga yozish
  var orderSheet = getOrCreateSheet("Buyurtmalar",
    ["Sana", "Ism", "Telefon", "Mahsulotlar", "Manzil matni", "Lat", "Lon", "Username"]);
  orderSheet.appendRow([
    new Date(),
    data.name || "",
    data.phone || "",
    data.items || "",
    data.address_text || "",
    data.lat || "",
    data.lon || "",
    data.username || ""
  ]);
  return ContentService.createTextOutput(JSON.stringify({ status: "ok" }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  if (e.parameter.action === "profile") {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Mijozlar");
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({})).setMimeType(ContentService.MimeType.JSON);
    }
    var values = sheet.getDataRange().getValues();
    for (var i = 1; i < values.length; i++) {
      if (String(values[i][0]) === String(e.parameter.user_id)) {
        var addresses = [];
        try { addresses = JSON.parse(values[i][3]); } catch (err) { addresses = []; }
        return ContentService.createTextOutput(JSON.stringify({
          name: values[i][1],
          phone: values[i][2],
          addresses: addresses
        })).setMimeType(ContentService.MimeType.JSON);
      }
    }
    return ContentService.createTextOutput(JSON.stringify({})).setMimeType(ContentService.MimeType.JSON);
  }

  // Standart holat: /hisobot uchun berilgan sanadagi buyurtmalarni qaytarish
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Buyurtmalar");
  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify([])).setMimeType(ContentService.MimeType.JSON);
  }
  var values = sheet.getDataRange().getValues();
  var headers = values[0];
  var targetDate = e.parameter.date;
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var row = {};
    for (var j = 0; j < headers.length; j++) row[headers[j]] = values[i][j];
    if (targetDate) {
      var d = new Date(row["Sana"]);
      var dStr = Utilities.formatDate(d, Session.getScriptTimeZone(), "yyyy-MM-dd");
      if (dStr !== targetDate) continue;
    }
    rows.push(row);
  }
  return ContentService.createTextOutput(JSON.stringify(rows)).setMimeType(ContentService.MimeType.JSON);
}
