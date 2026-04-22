#!/usr/bin/perl -w

#########################################
# bsheader.cgi v2.0 - GodStore edition
# Cart header iframe for GodStore
#########################################

use CGI qw(:standard);
use MIME::Base64;

### Read CartID Cookie ###
$ctemp=cookie('CartID');
@c_cookievalue=split(":", ("$ctemp"));
$id=shift(@c_cookievalue);
$items=shift(@c_cookievalue);
$cost=shift(@c_cookievalue);
$price='$' . sprintf("%.2f", $cost);

### Read SSOid Cookie ###
$stemp=cookie('SSOid');
$stemp=decode_base64($stemp);
@s_cookievalue=split(":", ("$stemp"));
$email=shift(@s_cookievalue);
$passwd=shift(@s_cookievalue);
$fullname=shift(@s_cookievalue);

if ($fullname eq '') {
	$fullname="Guest";
}

if ($items eq '') {
	$items="0";
}

print "Content-type: text/html\n\n";

print qq|<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      background: transparent;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 12px;
      color: #94a3b8;
      height: 30px;
      overflow: hidden;
    }
    body {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      padding: 0 16px;
    }
    .gs-user {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .gs-user svg { opacity: 0.6; }
    .gs-user strong { color: #e2e8f0; font-weight: 600; }
    .gs-dot { opacity: 0.3; }
    .gs-cart {
      display: flex;
      align-items: center;
      gap: 5px;
      color: #38bdf8;
      font-weight: 600;
    }
    .gs-cart svg { opacity: 0.9; }
    .gs-badge {
      background: #38bdf8;
      color: #0c1a27;
      font-size: 10px;
      font-weight: 800;
      border-radius: 9999px;
      padding: 1px 6px;
      min-width: 18px;
      text-align: center;
    }
  </style>
</head>
<body>
  <span class="gs-user">
    <svg viewBox="0 0 24 24" fill="none" width="13" height="13">
      <circle cx="12" cy="8" r="4" stroke="#94a3b8" stroke-width="2"/>
      <path d="M4 20c0-3.87 3.58-7 8-7s8 3.13 8 7" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
    </svg>
    <strong>$fullname</strong>
  </span>
  <span class="gs-dot">&#x2022;</span>
  <span class="gs-cart">
    <svg viewBox="0 0 24 24" fill="none" width="13" height="13">
      <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" stroke="#38bdf8" stroke-width="2" stroke-linejoin="round"/>
      <line x1="3" y1="6" x2="21" y2="6" stroke="#38bdf8" stroke-width="2"/>
      <path d="M16 10a4 4 0 01-8 0" stroke="#38bdf8" stroke-width="2"/>
    </svg>
    <span class="gs-badge">$items</span>
    item(s) &mdash; $price
  </span>
</body>
</html>|;
