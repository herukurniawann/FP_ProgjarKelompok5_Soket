# 📱 Multi-Realm Chat Application

## 📑 Dokumentasi

### 👥 Pembagian Tugas Antar Anggota Tim

| Nama Anggota                | NRP        | Tugas | GitHub Username                    |
| --------------------------- | ---------- | ----- | ---------------------------------- |
| Radhiyan Muhammad Hisan     | 5025211166 | Send private & group, realm | [@SanGit56](https://github.com/SanGit56) |
| Arfi Raushani Fikra         | 5025211084 |  |                                    |
| Muhammad Daffa Ashdaqfillah | 5025211015 |  | [@daf2a](https://github.com/daf2a) |
| Baihaqi Rizki Nurfajri      | 5025211044 |  |                                    |
| Najma Ulya Agustina         | 5025211239 |  |                                    |
| Heru Dwi Kurniawan          | 5025211055 |  |                                    |

### 📂 Repository Tugas di GitHub

🔗 [GitHub Repository](https://github.com/herukurniawann/FP_ProgjarKelompok5_Soket)

### 📝 Definisi Protokol Chat

#### 🗨️ Private Messaging

Format pesan:

```
send <sessionid> <username_to> <message>
```

Contoh:

```
send abc123 heru Hello, how are you?
```

#### 👥 Group Messaging

Format pesan:

```
sendgroup <sessionid> <group_name> <message>
```

Contoh:

```
sendgroup abc123 group1 Hello, everyone!
```

#### 📁 Send dan Receive File

Kirim file pribadi:

```
sendfile <sessionid> <username_to> <filename> \r\n\r\n<base64_file_content>
```

Contoh:

```
sendfile abc123 heru document.pdf \r\n\r\nJVBERi0xLjQKJ... (base64 content)
```

Kirim file ke grup:

```
sendgroupfile <sessionid> <group_name> <filename> \r\n\r\n<base64_file_content>
```

Contoh:

```
sendgroupfile abc123 group1 document.pdf \r\n\r\nJVBERi0xLjQKJ... (base64 content)
```

### 🌐 Definisi Protokol Pertukaran Antar Server Antar Realm

Kirim pesan antar realm:

```
sendrealm <username_from> <username_to> <message>
```

Contoh:

```
sendrealm alice heru Hello from another realm!
```

Kirim pesan grup antar realm:

```
sendgrouprealm <username_from> <group_name> <message>
```

Contoh:

```
sendgrouprealm alice group1 Hello group from another realm!
```

### 🏗️ Arsitektur Implementasi

- **Server 1:**
  - IP Address: `127.0.0.1`
  - Chat Port: `8889`
  - Realm Port: `8890`
- **Server 2:**
  - IP Address: `127.0.0.1`
  - Chat Port: `8888`
  - Realm Port: `8891`

### 🚀 Bagaimana Menjalankan Server dan Client

#### Menjalankan Server

1. **Server 1:**

   ```sh
   python server1/server.py
   ```

2. Server 2:
   ```sh
    python server2/server.py
   ```

#### Menjalankan Client

1. **Client 1:**

   ```sh
   python client1/main.py
   ```

2. **Client 2:**
   ```sh
   python client2/main.py
   ```

### ✅ Uji Awal dari Komunikasi

1. **Uji Private Messaging:**

   - Daftar dan login dengan akun berbeda di dua client.
   - Kirim pesan dari satu client ke client lain.
   - Verifikasi pesan diterima di client tujuan.

2. **Uji Group Messaging:**

   - Buat grup di salah satu client.
   - Kirim pesan ke grup tersebut.
   - Verifikasi pesan diterima oleh semua anggota grup.

3. **Uji Pengiriman File:**

   - Kirim file dari satu client ke client lain.
   - Verifikasi file diterima dan bisa diunduh di client tujuan.

4. **Uji Pesan Antar Realm:**
   - Kirim pesan dari client di server 1 ke client di server 2.
   - Verifikasi pesan diterima di client tujuan di server lain.
