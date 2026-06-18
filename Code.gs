/**
 * 韓鮮生 公關名單 App — Google Apps Script 後端 (Code.gs)
 * ------------------------------------------------------------------
 * 部署方式：以「網頁應用程式 (Web App)」部署
 *   - 執行身分 (Execute as)：我 (Me)
 *   - 誰可以存取 (Who has access)：任何人 (Anyone)
 * 部署後拿到的 /exec 網址，貼到 App 的「設定」畫面。
 *
 * 設計重點：
 *   - 一律用「標題名稱」對應欄位，不寫死欄號（可任意調整欄序）。
 *   - 自動偵測公關名單分頁：標題列同時含 SIGNATURE_HEADERS 兩個字。
 *   - 重複標題（例如兩個「備註」）只取「第一個出現」的那一欄。
 *   - 寫回時若出現分頁沒有的欄位（例如第一次的「要聯繫」），自動新增該欄。
 */

var SPREADSHEET_ID = '1c3LY_JC2z4tDEpd8x84J0uTNYIhjQ61Wz6t5IcU1ETM';
var SIGNATURE_HEADERS = ['帳戶名', '已發送邀約']; // 兩者都出現才判定是公關分頁
var ID_HEADER = '序'; // 每筆唯一識別

/** 找出公關名單分頁（依標題列特徵） */
function getSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    var sheet = sheets[i];
    var lastCol = sheet.getLastColumn();
    if (lastCol < 1) continue;
    var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(trim_);
    var matched = SIGNATURE_HEADERS.every(function (sig) {
      return headers.indexOf(sig) !== -1;
    });
    if (matched) return sheet;
  }
  throw new Error('找不到公關名單分頁（標題列需同時含「' + SIGNATURE_HEADERS.join('」與「') + '」）');
}

function trim_(v) { return String(v == null ? '' : v).trim(); }

/** 把儲存格值轉成可傳輸格式；日期格式化為 yyyy/MM/dd */
function formatCell_(v, tz) {
  if (v instanceof Date) {
    return Utilities.formatDate(v, tz, 'yyyy/MM/dd');
  }
  return v;
}

/** GET：回傳整份名單 { ok, headers, rows } */
function doGet(e) {
  try {
    var sheet = getSheet_();
    var tz = sheet.getParent().getSpreadsheetTimeZone();
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();

    if (lastRow < 2 || lastCol < 1) {
      return json_({ ok: true, headers: [], rows: [] });
    }

    var values = sheet.getRange(1, 1, lastRow, lastCol).getValues();
    var rawHeaders = values[0].map(trim_);

    // 去重後的標題清單（保留第一次出現順序）
    var headers = [];
    var seen = {};
    for (var c = 0; c < rawHeaders.length; c++) {
      var h = rawHeaders[c];
      if (h === '' || seen[h]) continue;
      seen[h] = true;
      headers.push(h);
    }

    var idColIdx = rawHeaders.indexOf(ID_HEADER); // 0-based
    var rows = [];
    for (var r = 1; r < values.length; r++) {
      var rowVals = values[r];
      var idVal = idColIdx === -1 ? '' : rowVals[idColIdx];
      if (idVal === '' || idVal === null) continue; // 略過沒有序號的空列

      var obj = { _row: r + 1 };
      var used = {};
      for (var c2 = 0; c2 < rawHeaders.length; c2++) {
        var hh = rawHeaders[c2];
        if (hh === '' || used[hh]) continue; // 重複標題只取第一個
        used[hh] = true;
        obj[hh] = formatCell_(rowVals[c2], tz);
      }
      rows.push(obj);
    }

    return json_({ ok: true, headers: headers, rows: rows });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

/** POST：收 { 序, updates:{標題:值} }，依標題寫回 */
function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    var id = body[ID_HEADER];
    var updates = body.updates || {};
    if (id === undefined || id === null || id === '') {
      return json_({ ok: false, error: '缺少序號（' + ID_HEADER + '）' });
    }

    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      var sheet = getSheet_();
      var lastRow = sheet.getLastRow();
      var lastCol = sheet.getLastColumn();
      var rawHeaders = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(trim_);

      // 標題 -> 第一個出現的欄索引 (1-based)
      var colOf = {};
      for (var c = 0; c < rawHeaders.length; c++) {
        var h = rawHeaders[c];
        if (h === '' || (h in colOf)) continue;
        colOf[h] = c + 1;
      }

      var idCol = colOf[ID_HEADER];
      if (!idCol) return json_({ ok: false, error: '分頁沒有「' + ID_HEADER + '」欄' });

      // 以「序」定位列
      var idValues = sheet.getRange(2, idCol, Math.max(lastRow - 1, 0), 1).getValues();
      var targetRow = -1;
      for (var i = 0; i < idValues.length; i++) {
        if (String(idValues[i][0]) === String(id)) { targetRow = i + 2; break; }
      }
      if (targetRow === -1) return json_({ ok: false, error: '找不到序號 ' + id + ' 的列' });

      var applied = {};
      for (var key in updates) {
        if (!updates.hasOwnProperty(key)) continue;
        var col = colOf[key];
        if (!col) {
          // 自動新增欄（放最後）
          lastCol = lastCol + 1;
          sheet.getRange(1, lastCol).setValue(key);
          colOf[key] = lastCol;
          col = lastCol;
        }
        sheet.getRange(targetRow, col).setValue(updates[key]);
        applied[key] = updates[key];
      }
      SpreadsheetApp.flush();
      return json_({ ok: true, '序': id, _row: targetRow, applied: applied });
    } finally {
      lock.releaseLock();
    }
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
