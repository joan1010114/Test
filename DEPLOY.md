# 韓鮮生 公關名單 App — 部署與操作手冊

> 給使用者（手機操作為主）。照步驟做即可。架構：
> 手機 App（`index.html`） → Google Apps Script（`Code.gs`） → Google 試算表（唯一資料源）

---

## 任務 1：把 `Code.gs` 部署成 Apps Script 網頁應用程式

> 這一步在「電腦」上做比較順（要授權、複製網址）。手機也能做，但畫面較擠。

### 1-1 開啟試算表的 Apps Script
1. 用瀏覽器打開那份試算表（ID：`1c3LY_JC2z4tDEpd8x84J0uTNYIhjQ61Wz6t5IcU1ETM`）。
2. 上方選單 **「擴充功能」→「Apps Script」**。會開新分頁，進到程式碼編輯器。

### 1-2 貼上程式碼
1. 左側若有 `Code.gs`（或 `程式碼.gs`），點它。
2. 把裡面內容**全選刪除**，貼上本專案 `Code.gs` 的全部內容。
3. 按上方 **磁碟片圖示（儲存）**。

### 1-3 部署成網頁應用程式
1. 右上角 **「部署」→「新增部署作業」**。
2. 點齒輪「選取類型」→ 選 **「網頁應用程式」**。
3. 設定：
   - 說明：隨意（例如 `pr-v1`）
   - **執行身分（Execute as）**：`我（你的 Google 帳號）`
   - **誰可以存取（Who has access）**：`任何人（Anyone）`
4. 按 **「部署」**。

### 1-4 第一次授權（會出現警告，照下面點就對了）
> 因為這支腳本會動你的試算表，Google 會要你授權。畫面文字大致如下：

1. 跳出視窗 → 按 **「授權存取」/「Authorize access」**。
2. 選你的 Google 帳號。
3. 出現 **「Google 尚未驗證這個應用程式」/「This app isn't verified」** → 點左下角 **「進階」/「Advanced」**。
4. 點 **「前往『（你的專案名）』(不安全)」/「Go to … (unsafe)」**。
   - 這是你自己寫的腳本，安全。
5. 看到權限清單 → 拉到底按 **「允許」/「Allow」**。

### 1-5 複製 `/exec` 網址
- 授權完會顯示 **「網頁應用程式」網址**，結尾是 **`/exec`**。
- 按 **「複製」**。這串就是 App 設定要貼的網址。**先存起來（貼到備忘錄）。**

> ✅ 驗證後端：直接用瀏覽器打開那個 `/exec` 網址。應該看到一串 JSON：`{"ok":true,"headers":[...],"rows":[...]}`。
> 看到 `rows` 有資料就代表後端成功。

### （重要）之後改了 `Code.gs` 要怎麼更新？
- 改完存檔 → **「部署」→「管理部署作業」→** 在現有那筆按 **鉛筆（編輯）→ 版本選「新版本」→ 部署**。
- **`/exec` 網址不會變**，App 不用重設。

---

## 任務 2：把 `index.html` 部署到 Cloudways，子網域 `pr.52ec.tw`

### 2-1 程式碼已在 GitHub
- 本 repo 已含 `index.html`、`.htaccess`。確認你要部署的分支是最新的（本次工作分支：`claude/hansensheng-pr-app-deploy-2w2epq`，正式上線可合併到 `main`）。

### 2-2 Cloudways 建立／設定應用程式
1. 登入 Cloudways → 進入你的 Server（IP `139.162.122.239`）。
2. 用既有 App 或新增一個 **PHP/靜態** 應用程式給這個站。
3. 進該 App → **Application Settings**，確認 **Webroot** 指向放 `index.html` 的資料夾（通常 `public_html`）。

### 2-3 用 Git Pull 部署
1. App 左側 **Deployment Via Git**。
2. 貼上你的 GitHub repo（私有 repo 需先把 Cloudways 顯示的 **Deploy Key / SSH key 加到 GitHub** repo 的 Deploy keys）。
3. Branch 填要上線的分支 → **Pull**。
4. 之後每次更新：回這頁按 **Pull** 即可。

### 2-4 子網域 `pr.52ec.tw` 設定
1. **DNS（在 52ec.tw 網域的 DNS 服務商）**：
   - 新增一筆 **A 記錄**：主機名 `pr` → 指向 `139.162.122.239`。
   - 等生效（幾分鐘到數十分鐘）。
2. **Cloudways 綁網域**：
   - App → **Domain Management** → 把 `pr.52ec.tw` 設為網域（或加為附加網域）。
3. **SSL**：
   - App → **SSL Certificate** → Let's Encrypt → 填 `pr.52ec.tw` → 安裝。開啟 **Force HTTPS**。

### 2-5 預設首頁 / `.htaccess`（你在 Tokyo 站踩過的坑）
- 本 repo 已附 `.htaccess`，內含 `DirectoryIndex index.html`，會強制以 `index.html` 為首頁，避免 Cloudways 預設找 `index.php` 而 404 或跑到別的頁。
- 若打開 `pr.52ec.tw` 沒看到 App：確認 `.htaccess` 有被 pull 下來（隱藏檔，Git 會帶；FileZilla 要開「顯示隱藏檔」才看得到），且 Webroot 正確。

---

## 任務 3：連線測試（在手機上）

1. 手機瀏覽器打開 `https://pr.52ec.tw`。
2. 第一次會看到「還沒設定資料來源」→ 點右上角 **⚙** 或「前往設定」。
3. 貼上任務 1 拿到的 **`/exec` 網址** → 按 **「儲存並載入名單」**。
4. 應載入約 **82 筆**卡片。右上小圓點變 **綠色（已同步）**。
5. 隨便點一張卡 → 切一個開關（例如「要聯繫」）→ 打開試算表確認那一格被寫入（`TRUE` 或日期）。
6. 建議：iPhone Safari「加入主畫面」，當 App 用。

### 疑難排解
- **載入不到 / 一直離線**：先用瀏覽器開 `/exec` 看有沒有 JSON；沒有就回任務 1 重新部署＋重新授權。
- **寫不回去**：多半是 `/exec` 貼錯，或 `Code.gs` 改過但沒「新版本」重新部署。
- **找不到分頁**：後端靠標題列同時含「帳戶名」和「已發送邀約」判定分頁；確認那一列標題沒被改掉。

---

## 任務 4：複製給其他客戶品牌

換品牌時，要改的地方很少：

1. **信件範本**（`index.html` 最上方 JS）：
   - `MAIL_SUBJECT`：主旨。
   - `mailBody(name)`：信件內文。
2. **品牌外觀**（可選）：`index.html` 的 `<title>`、CSS 變數 `--brand`（主色）、頂列文字「韓鮮生 公關名單」。
3. **資料來源**：
   - `Code.gs` 的 `SPREADSHEET_ID` 換成新品牌試算表 ID。
   - 重新部署 → 拿新 `/exec` → 在新站台設定貼上。
4. **欄位／分頁特徵**（只有當新品牌試算表欄位名不同時才需要）：
   - `index.html` 的 `F = {...}` 欄位名稱對應。
   - `Code.gs` 的 `SIGNATURE_HEADERS`（分頁辨識用的兩個標題）與 `ID_HEADER`（唯一識別欄）。
5. 新站台給新子網域（例如 `pr-客戶.52ec.tw`），重複任務 2。

> 因為全程用「標題名稱」對應、欄序可變，換品牌通常只動上面 1～3 即可。
