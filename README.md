# coolToReminder

這是一個用 Python 撰寫的 CLI 工具，用於將 NTU Cool (Canvas LMS) 上的作業和事件，自動同步到你的 Microsoft To Do 待辦清單中，並且自動設定提醒時間。

支援增量同步，如果 Canvas 上的作業資訊（例如截止日期）有變更，這個工具會自動在 To Do 中更新對應的任務。

## 特色
- 支援增量同步（不重複新增任務）
- 自動設定提醒時間
- 背景定時執行（透過 Linux systemd）
- 使用 Device Code Flow，適用於無圖形介面的伺服器與工作站

---

## 快速開始 (Windows 本地測試)

### 1. 安裝環境
確保你有安裝 Python 3.8 以上版本，然後安裝相依套件：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 設定檔
複製範例設定檔：
```bash
copy .env.example .env
```
編輯 `.env`，填入以下資訊：
- `AZURE_CLIENT_ID`: (見下方 Azure App 註冊)
- `AZURE_TENANT_ID`: (見下方 Azure App 註冊)
- `ICAL_FEED_URL`: NTU Cool 行事曆右下角的「行事曆摘要」網址

### 3. 初次認證
執行以下指令進行微軟帳號登入：
```bash
python main.py auth
```
終端機會顯示一組代碼和一個網址（例如 `https://microsoft.com/devicelogin`），請用瀏覽器打開該網址，輸入代碼並登入你的微軟帳號。成功後，Token 會自動快取存入本地的 `.token_cache.json`。

### 4. 執行同步
```bash
python main.py sync
```
這會抓取 iCal，並在你的 Microsoft To Do 建立一個名為「NTU Cool 作業」的清單（名稱可在 `.env` 更改），接著把作業同步進去。

---

## 遠端部署 (Ubuntu 24.04 VM)

1. SSH 進入你的 Ubuntu VM。
2. Clone 這個 Repo：
   ```bash
   git clone https://github.com/otaiwan1/coolToReminder.git /opt/coolToReminder
   cd /opt/coolToReminder
   ```
3. 設定環境：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # 編輯 .env 填入資料 (nano .env)
   ```
4. 初次認證：
   ```bash
   python main.py auth
   # 在你的電腦瀏覽器上完成 device code flow 登入
   ```
5. 自動設定背景執行 (Systemd Timer)：
   工具內建了自動部署指令，會依照 `.env` 內的 `SYNC_INTERVAL_MINUTES` 設定背景定期執行的頻率（預設為 60 分鐘）。請**使用 sudo** 執行以下指令：
   ```bash
   sudo venv/bin/python main.py deploy
   ```
   執行成功後，工具就會自動在背景定時執行。你可以隨時使用以下指令查看即時的同步紀錄：
   ```bash
   sudo journalctl -u coolsync.service -f
   ```

---

## Azure App 註冊步驟

由於 Microsoft Graph API 需要應用程式身分，你必須註冊一個自己的 Azure App：

1. 前往 [Azure Portal - App registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) 並登入（使用你要存放 To Do 的那個微軟帳號）。
2. 點擊 **New registration**。
   - 名稱：`coolToReminder`
   - Supported account types：如果你用的是學校帳號，選 `Accounts in any organizational directory and personal Microsoft accounts`；如果是個人信箱，選 `Personal Microsoft accounts only`。
3. 註冊完成後，在 **Overview** 頁面複製 **Application (client) ID** 和 **Directory (tenant) ID**，貼到 `.env` 中。（如果上一題選了 Personal accounts，Tenant ID 在 `.env` 可以留空或填 `common`）。
4. 在左側選單點擊 **Authentication**。
   - 往下捲動找到 **Advanced settings** -> **Allow public client flows**，選 **Yes**。(非常重要，否則 Device Code Flow 會失敗)。
5. 在左側選單點擊 **API permissions**。
   - 點擊 **Add a permission** -> **Microsoft Graph** -> **Delegated permissions**。
   - 搜尋並勾選 `Tasks.ReadWrite`。
   - 點擊 **Add permissions**。
