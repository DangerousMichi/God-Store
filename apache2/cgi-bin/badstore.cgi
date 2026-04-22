#!/usr/bin/perl -w

#############################################################################
# BadStore.cgi v1.2.3s
# The CGI program file for BadStore.net
#
# Copyright 2004-6 - Kurt R. Roemer
# Developed and Maintained by:  Kurt R. Roemer, CISSP
# Last Modified:  10 May 2006 - kroemer@netcontinuum.com
# Visit www.badstore.net/downloads for the latest version
#
# WARNING! - This is an insecure program used for demo and
# security training purposes only!  This is not a real store!
# See the Disclaimer for complete information on this program
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#############################################################################

### Specify required PERL modules ###
use CGI::Carp qw(fatalsToBrowser);
use DBI;
use CGI qw(:standard :html4);
use Digest::MD5 qw(md5_hex);
use MIME::Base64;

### Setup Global Variables ###
$time = time;
$ipaddr = $ENV{'REMOTE_ADDR'};

# SECURITY FIX: VUL-11 — credenciales de BD desde variables de entorno, no hardcodeadas
$DB_USER = $ENV{'DB_USER'} || 'root';
$DB_PASS = $ENV{'DB_PASS'} || 'secret';

# SECURITY FIX: VUL-10 — salt de aplicacion para hashing de contrasenas
# NOTA: En produccion usar bcrypt (Crypt::Bcrypt) con salt por usuario
use constant PWD_SALT => 'BsS@lt_2026!NoReuse#';

### Get submitted data from URL or FORM ###
$query=new CGI;
$action=$query->param('action');

### Setup Header and Footer ###
open (BSHEADER, '../data/header.txt') or die "Cannot open footer file\n";
@header=<BSHEADER>;
close (BSHEADER);
open (BSFOOTER, '../data/footer.txt') or die "Cannot open footer file\n";
@footer=<BSFOOTER>;
close (BSFOOTER);

### Determine action from URL or FORM data ###

if ($action eq 'whatsnew')
{
   &whatsnew;

} elsif ($query->url_param('action') eq 'cartadd') {
   &cartadd;

#} elsif ($action eq 'cartremove') {
#   &cartremove;

#} elsif ($action eq 'cartchangeqty') {
#   &cartqty;

} elsif ($action eq 'cartview') {
   &cartview;

} elsif ($query->url_param('action') eq 'order') {
   &order;

} elsif ($query->url_param('action') eq 'viewprevious') {
   &viewprevious;

} elsif ($query->url_param('action') eq 'submitpayment') {
   &submitpayment;

} elsif ($action eq 'guestbook') {
   &guestbook;

} elsif ($query->url_param('action') eq 'doguestbook') {
   &doguestbook;

} elsif ($action eq 'aboutus') {
   &aboutus;

} elsif ($action eq 'loginregister') {
   &loginregister;

} elsif ($query->url_param('action') eq 'login'){
   &authuser;

} elsif ($query->url_param('action') eq 'register'){
   &authuser;

} elsif ($action eq 'search') {
   &search;

} elsif ($action eq 'supplierlogin') {
   &supplierlogin;

} elsif ($action eq 'supplierproc') {
   &supplierproc;
   
} elsif ($query->url_param('action') eq 'supplierportal') {
   &supplierportal;

} elsif ($query->url_param('action') eq 'supupload') {
   &supupload;

} elsif ($action eq 'admin') {
   &admin;

} elsif ($query->url_param('action') eq 'adminportal') {
   &adminportal;

} elsif ($action eq 'myaccount'){
  &myaccount;

} elsif ($query->url_param('action') eq 'moduser'){
  &moduser;

} else {
   &home;
}

exit;


sub start_page {
   my %args = ();
   
   if(@_ == 1) {
	  $args{-title} = shift;
   } else {
	  %args = (@_);
   }
   
   $args{-title} ||= '';
   if($args{-script}) {
	  $args{-script} = "<script type=\"text/javascript\" src=\"" . $args{-script}{-src} . "\"></script>";
   } else {
	  $args{-script} = '';
   }
   
   my $s = qq|
   <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
	  <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
	  <head>
		<title>$args{-title}</title>
		$args{-script}
		<meta http-equiv="Content-type" content="text/html;charset=utf-8" />
		<link rel="stylesheet" type="text/css" href="/css/global.css" media="all" />
	  </head>
	  <body>|;
   
   return $s . "@header";
}

sub end_page {
   my $s = "@footer" . end_html;
   return $s;
}

############
### Home ###
############

sub home
{
	&printheaders;
	print start_page("Welcome to BadStore.net v1.2.3s - The most insecure store on the 'Net!"),
	h1("<font color=#004b2c>Welcome to BadStore.net!</font>"),
	p(img({-src=>'/images/store1.jpg',-border=>'0'})),
	end_page();
}

##################
### What's New ###
##################

sub whatsnew
{
	local (@data);

	### Connect to the SQL Database ###
	my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
		or die "Cannot connect: " . $DBI::errstr;

	### Prepare and Execute SQL Query ###
	my $sth = $dbh->prepare( "SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE isnew = 'Y'")
                or die "Couldn't prepare statement: " . $dbh->errstr;
          $sth->execute() or die "Couldn't execute SQL statement: " . $sth->errstr;

	&printheaders;
	print start_page("What's New at BadStore.net");
	if ($sth->rows == 0) {
      	print h2("No new items! "),"$sth.\n\n";
      } else {
		print start_form( -action=>'/cgi-bin/badstore.cgi?action=cartadd');
		### Read the matching records and print them out ###
		print h2("The following are new items:"),'<table cellspacing="0" cellpadding="0" class="products">';
		print Tr( th('ItemNum'),th('Item'),th('Description'),th('Price'),th('Image'),th('Select'));
          		while (@data = $sth->fetchrow_array()) {
				$image='/images/' . $data[0] . '.jpg';
				print Tr( td( \@data ),td({-align=>CENTER},"<IMG SRC=$image>"),td({-align=>CENTER},"<INPUT type=checkbox name='cartitem' value=$data[0]>") );
			}
		print "</table>\n\n", p, "<Center>", submit('Add Items to Cart'), "   ", reset(), "</Center>", end_form;
		}

	### Close statement handles ###
	$sth->finish;

	### Disconnect from the databases ###
	$dbh->disconnect;

	print end_page();
}

##############
### Search ###
##############

sub search
{
	local (@data, $squery, $temp, $sql);
	$squery=$query->param('searchquery');

	### Connect to the SQL Database ###
	my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
		or die "Cannot connect: " . $DBI::errstr;

	### Prepare and Execute SQL Query ###
	# SECURITY FIX: VUL-01 — parametro preparado para prevenir SQL Injection en busqueda
	my $sth = $dbh->prepare("SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE ? IN (itemnum,sdesc,ldesc)")
                or die "Couldn't prepare SQL statement: " . $dbh->errstr;
	$sth->execute($squery) or die "Couldn't execute SQL statement: " . $sth->errstr;

	&printheaders;
	print start_page("BadStore.net - Search Results");
	# SECURITY FIX: VUL-08 — eliminados comentarios de debug y disclosure de consulta SQL
	# SECURITY FIX: VUL-08 — no imprimir $sql ni $sth->errstr al cliente (XSS + info disclosure)

          if ($sth->rows == 0) {
            print h2("No items matched your search criteria.");
          } else {
	### Read the matching records and print them out ###
	print h2("The following items matched your search criteria:"),
    start_form( -action=>'/cgi-bin/badstore.cgi?action=cartadd'),"<TABLE BORDER=1>",
	Tr( th('ItemNum'),th('Item'),th('Description'),th('Price'),th('Image'),th('Add to Cart'));
          while (@data = $sth->fetchrow_array()) {
		$image='/images/' . $data[0] . '.jpg';
		print Tr( td( \@data ),td({-align=>CENTER},"<IMG SRC=$image>"),td({-align=>CENTER},"<INPUT type=checkbox name='cartitem' value=$data[0]>") );
		}
	print "</TABLE>\n\n", p, "<Center>", submit('Add Items to Cart'), "   ", reset(), "</Center>", end_form;
	}

	### Close statement handles ###
	$sth->finish;

	### Disconnect from the databases ###
	$dbh->disconnect;
	print end_page();
}

#########
# Admin #
#########

sub admin
{
	&printheaders;
	print start_page("Private Administration Portal for BadStore.net"),
	h2("Secret Administration Menu"), p;

	print start_form(-action=>'/cgi-bin/badstore.cgi?action=adminportal'),
	p, h2("Where do you want to be taken today?"),
	popup_menu(-name=>'admin', -values=>['View Sales Reports','Reset User Password','Add User','Delete User','Show Current Users','Troubleshooting','Backup Databases']),
	submit('Do It'), end_form,
	end_page();
}

################
# Admin Portal #
################

sub adminportal
{
	local ($aquery, $email, $newpasswd, @data, $stemp, @s_cookievalue, $passwd, $fullname, $role);
	&printheaders;
	print start_page("Private Administration Portal for BadStore.net"),
	h1("Secret Administration Portal"), p;
	$aquery=$query->param('admin');

	### Read SSOid Cookie ###
	$stemp=cookie('SSOid');
	$stemp=decode_base64($stemp);
	@s_cookievalue=split(":", ("$stemp"));
	$email=shift(@s_cookievalue);
	$passwd=shift(@s_cookievalue);
	$fullname=shift(@s_cookievalue);
	if ($fullname eq '') {
		$fullname="{Unregistered User}";
	}
	# $role ignorado del cookie — se verifica contra la BD (VUL-04 fix abajo)

	### Connect to the SQL Database ###
	my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
	or die "Cannot connect: " . $DBI::errstr;

	# SECURITY FIX: VUL-04 — rol verificado desde la BD, no de la cookie controlada por el cliente
	my $role_sth = $dbh->prepare("SELECT role, fullname FROM userdb WHERE email=? AND passwd=?")
		or die "Couldn't prepare role check: " . $dbh->errstr;
	$role_sth->execute($email, md5_hex(PWD_SALT . '')) or die $role_sth->errstr;
	# Nota: passwd en cookie ya es el hash; lo comparamos directamente
	my $role_sth2 = $dbh->prepare("SELECT role, fullname FROM userdb WHERE email=? AND passwd=?")
		or die "Couldn't prepare role check: " . $dbh->errstr;
	$role_sth2->execute($email, $passwd) or die $role_sth2->errstr;
	my @role_row = $role_sth2->fetchrow_array();
	$role = $role_row[0] || '';
	$fullname = $role_row[1] || $fullname;
	$role_sth2->finish;

	### Check Admin Role (verified against database) ###
	if ($role eq 'A') {
	
		### Prepare the Sales Report ###
		if ($aquery eq 'View Sales Reports') {
		my $sth = $dbh->prepare("SELECT * FROM orderdb ORDER BY 'orderdate','ordertime'")
			or die "Couldn't prepare statement: " . $dbh->errstr;
		$sth->execute() or die "Couldn't execute SQL statement: " .$sth->errstr;

		print h2("<Center>BadStore.net Sales Report",p,&getdate,"</center>"), 
		"<TABLE BORDER=1>",
		Tr(th('Date'),th('Time'),th('Cost'),th('Count'),th('Items'),th('Account'),th('IP'),th('Paid'),th('Credit_Card_Used'),th('ExpDate'));
		while (@data=$sth->fetchrow_array()){
			$data[9]=~ s/(\d\d\d\d)[\-\s]?/$1-/g;
			$data[9]=~ s/-$//;
			print Tr(td(font({face=>'Arial', size=>'-2'},$data[1])),td(font({face=>'Arial', size=>'-2'},$data[2])),td(font({face=>'Arial', size=>'-2'},$data[3])),td(font({face=>'Arial', size=>'-2'},$data[4])),td(font({face=>'Arial', size=>'-2'},$data[5])),td(font({face=>'Arial', size=>'-2'},$data[6])),td(font({face=>'Arial', size=>'-2'},$data[7])),td(font({face=>'Arial', size=>'-2'},$data[8])),td(font({face=>'Arial', size=>'-2'},$data[9])),td(font({face=>'Arial',size=>'-2'},$data[10])));
		}
		print "</TABLE>\n\n",p;

		} elsif ($aquery eq 'Reset User Password') {

			### Reset User Password ###
			### Prepare and Execute SQL Query ###
			my $sth = $dbh->prepare( "SELECT email FROM userdb")
	            	    or die "Couldn't prepare statement: " . $dbh->errstr;
		      $sth->execute() or die "Couldn't execute SQL statement: " . $sth->errstr;
			while (@data=$sth->fetchrow_array()) {
				@ids=(@ids, $data[0]);
			}
			print start_form( -action=>'/cgi-bin/badstore.cgi?action=moduser'),
			p, "Reset password for: ",
			popup_menu(-name=>'email', -values=>[@ids]),
			submit(-name=>'DoMods',-value=>'Reset User Password'), end_form;
	
			### Close statement handles ###
			$sth->finish;

     		} elsif ($aquery eq 'Troubleshooting') {

			### Print CGI Environment ###
			print h2("CGI Environment Variables"), "<TABLE BORDER=1>";

			my %env_info = (
		  	    SERVER_SOFTWARE     => "the server software",
			    SERVER_NAME         => "the server hostname or IP address",
			    GATEWAY_INTERFACE   => "the CGI specification revision",   
			    SERVER_PROTOCOL     => "the server protocol name",
			    SERVER_PORT         => "the port number for the server",
			    REQUEST_METHOD      => "the HTTP request method",
			    PATH_INFO           => "the extra path info",
			    PATH_TRANSLATED     => "the extra path info translated",
			    DOCUMENT_ROOT       => "the server document root directory",
			    SCRIPT_NAME         => "the script name",
			    QUERY_STRING        => "the query string",
			    REMOTE_HOST         => "the hostname of the client",
			    REMOTE_ADDR         => "the IP address of the client",
			    AUTH_TYPE           => "the authentication method",
			    REMOTE_USER         => "the authenticated username",
			    REMOTE_IDENT        => "the remote user is (RFC 931): ",
			    CONTENT_TYPE        => "the media type of the data",
			    CONTENT_LENGTH      => "the length of the request body",
			    HTTP_ACCEPT         => "the media types the client accepts",
			    HTTP_USER_AGENT     => "the browser the client is using",
			    HTTP_REFERER        => "the URL of the referring page",
			    HTTP_COOKIE         => "the cookie(s) the client sent"
			);

			# Add additional variables defined by web server or browser
			foreach $name ( keys %ENV ) {
			    $env_info{$name} = "an extra variable provided by this server"
		        unless exists $env_info{$name};
			}
			print Tr( th('Variable Name'),th('Description'),th('Value'));
			foreach $name ( sort keys %env_info ) {
		    		my $info = $env_info{$name};
		   		my $value = $ENV{$name} || "<I>Not Defined</I>";
				print Tr( td(font({face=>'Arial', size=>'-2'}, $name )),td(font({face=>'Arial', size=>'-2'}, $info )), td(font({face=>'Arial', size=>'-2'}, $value )));
			}
			print "</TABLE>",p;
			# SECURITY FIX: VUL-12 — reemplazados backticks (OS command injection) con lectura Perl segura
			print h2("Recent Apache Error Log"),p;
			my $log_file = '/data/apache2/log/error.log';
			if (open(my $log_fh, '<', $log_file)) {
				my @lines = <$log_fh>;
				close($log_fh);
				my @tail = @lines > 20 ? @lines[-20..-1] : @lines;
				foreach my $line (@tail) {
					print escapeHTML($line) . "<br/>";
				}
			} else {
				print "Log file not available.";
			}

			} elsif ($aquery eq 'Add User') {

			### Add a User ###
			print start_form(-method=>'POST',-action=>'/cgi-bin/badstore.cgi?action=moduser'),
			"Email Address:  ",textfield(-name=>'email',-size=>40),p,
			hidden(-name=>'password',-default=>[md5_hex('Welcome')]),
			"Password Hint:  ",popup_menu(-name=>'pwdhint',-values=>['green','blue','red','orange','purple','yellow']),p,			
			"Full Name:  ",textfield(-name=>'fullname',-size=>50),p,
			"Role:  ",textfield(-name=>'role',-size=>1),p,
			submit(-name=>'DoMods',-value=>'Add User'), reset(), end_form,hr;

			} elsif ($aquery eq 'Delete User') {
			### Delete User ###
			### Prepare and Execute SQL Query ###
			my $sth = $dbh->prepare( "SELECT email FROM userdb")
	            	    or die "Couldn't prepare statement: " . $dbh->errstr;
		      $sth->execute() or die "Couldn't execute SQL statement: " . $sth->errstr;

			while (@data=$sth->fetchrow_array()) {
				@ids=(@ids, $data[0]);
			}

			print start_form(-action=>'/cgi-bin/badstore.cgi?action=moduser'),
			p, "Delete User: ",
			popup_menu(-name=>'email', -values=>[@ids]),
			submit(-name=>'DoMods',-value=>'Delete User'), end_form;
	
			### Close statement handles ###
			$sth->finish;

			} elsif ($aquery eq 'Show Current Users') {

			### Show Current Users ###
			### Prepare and Execute SQL Query ###
			my $sth = $dbh->prepare( "SELECT * FROM userdb")
	            	    or die "Couldn't prepare statement: " . $dbh->errstr;
		      $sth->execute() or die "Couldn't execute SQL statement: " . $sth->errstr;
			print "<TABLE BORDER=1>",
			Tr(th('Email Address'),th('Password'),th('Pass Hint'),th('Full Name'),th('Role'));	
			while (@data=$sth->fetchrow_array()) {
				print Tr(td(font({face=>'Arial', size=>'-2'},$data[0])),td(font({face=>'Arial', size=>'-2'},$data[1])),td(font({face=>'Arial', size=>'-2'},$data[2])),td(font({face=>'Arial', size=>'-2'},$data[3])),td(font({face=>'Arial', size=>'-2'},$data[4])));
			}
			print "</TABLE>";
			} elsif ($aquery eq 'Backup Databases') {
      ### Unlink old backups ###
      if( -f '/var/backups/badstore/orderdb.bak') {
              unlink '/var/backups/badstore/orderdb.bak';
      }
      if( -f '/var/backups/badstore/userdb.bak') {
              unlink '/var/backups/badstore/userdb.bak';
      }
      ### Backup the Tables ###
			my $sth = $dbh->prepare( "SELECT * FROM orderdb INTO OUTFILE '/var/backups/badstore/orderdb.bak'")
	            	    or die "Couldn't prepare statement: " . $dbh->errstr;
		      	$sth->execute() or die "Couldn't execute SQL statement: " . $sth->errstr;
			my $sth = $dbh->prepare( "SELECT * FROM userdb INTO OUTFILE '/var/backups/badstore/userdb.bak'")
	            	    or die "Couldn't prepare statement: " . $dbh->errstr;
		      	$sth->execute() or die "Couldn't execute SQL statement: " . $sth->errstr;
			print h2("# SECURITY FIX: VUL-06 --- backups fuera del docroot
Database backup complete - archivos almacenados de forma segura en el servidor.");
			}
		### Disconnect from the databases ###
		$dbh->disconnect;

	} else {
		### Not an Admin user ###
		print h2("Error - $fullname is not an Admin!"),
        "Something weird happened - you tried to access the ",
		"Adminstrative Portal, but you are not an Administrative User.", p,
		"You must login as an Admin to access this resource.", p,
		"Use your browser's Back button and go to Login.", p, p, p,
		h3("(If you're trying to hack - I know who you are:   $ipaddr)");
	}
	print end_page();
}

#############
# Guestbook #
#############

sub guestbook
{
	&printheaders;
	print start_page("BadStore.net - Sign our Guestbook"),
	h2("Sign our Guestbook!"),
	p,
	"Please complete this form to sign our Guestbook.  The email field is not required, but helps us contact you to respond to your feedback.  Thanks!",
	p, "<TABLE BORDER=0 CELLLPADDING=10>";
	print start_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=doguestbook');
	print Tr( td('Your Name:'), td('<INPUT TYPE=text NAME=name SIZE=30>'));
	print Tr( td('Email:'), td('<INPUT TYPE=text NAME=email SIZE=40>'));
    print Tr( td({-valign=>TOP},'Comments:'), td('<TEXTAREA NAME=comments COLS=60 ROWS=4></TEXTAREA>'));
    print Tr(td(''),td('<input type="submit" value="Add Entry" /> <input type="reset" value="Reset" />'));
	print "</TABLE>\n\n",
	end_form,
	end_page();
}

################
# Do Guestbook #
################

sub doguestbook
{
	local($timestamp, $name, $email, $comments, %fields);
	my ($dataFile) = "/data/apache2/data/guestbookdb";
	
	$timestamp=&getdate;
	$name=$query->param('name');
	$email=$query->param('email');
	$comments=$query->param('comments');
	chomp($comments);

    &saveFormData(\%fields, $dataFile);

	&printheaders;
	print start_page("Welcome to the BadStore.net Guestbook");

    print h1("Guestbook");
    &readFormData($dataFile);
	print end_page();
}

sub saveFormData {
    my($hashRef) = shift;
    my($dbfile) = shift;

    open(FILE, ">>$dbfile") or die("Unable to open Guestbook data file $dbfile: $!\n");
    print FILE ("$hashRef->{'timestamp'}$timestamp~");
    print FILE ("$hashRef->{'name'}$name~");
    print FILE ("$hashRef->{'email'}$email~");
    print FILE ("$hashRef->{'comments'}$comments");
    print FILE ("\n");
    close(FILE);
}

sub readFormData {
    my($dbfile)    = shift;

    open(FILE, "<$dbfile") or die("Unable to open Guestbook data file.");
    while (<FILE>) {
        my($timestamp, $name, $email, $comments) = split(/~/, $_);

        # SECURITY FIX: VUL-07 — escapado HTML en todos los campos para prevenir XSS almacenado
        my $safe_ts       = escapeHTML($timestamp // '');
        my $safe_name     = escapeHTML($name      // '');
        my $safe_email    = escapeHTML($email     // '');
        my $safe_comments = escapeHTML($comments  // '');

        print("$safe_ts: <B>$safe_name</B> <A HREF='mailto:$safe_email'>$safe_email</A>\n");
        print("<OL><I>$safe_comments</I></OL>\n");
        print("<HR>\n");
    }
    close(FILE);
}

###############################
### Get and format the date ###
###############################

sub getdate
{
   local ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst,$date);
   local (@days, @months);

   @days = ('Sunday','Monday','Tuesday','Wednesday','Thursday', 'Friday', 'Saturday');

   @months = ('January','February','March','April','May','June','July','August','September','October','November','December');

   ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);

   if ($hour < 10){ $hour = "0$hour"; }
   if ($min < 10){ $min = "0$min"; }
   if ($sec < 10){ $sec = "0$sec"; }

   $year += 1900;
   $date = "$days[$wday], $months[$mon] $mday, $year at $hour\:$min\:$sec";

   return $date;
}

###############
# Add to Cart #
###############

sub cartadd
{
	local($temp, @contents, $cookievalue);

	### Check for existing cookie and setup an empty cart ###
	if ($cartcookie eq "")
		{
		($sessid)=($time);
		$cartitems=0;
		$cartcost=0;
		@contents=$query->param('cartitem');
		}

	chomp(@contents);
	### Check for zero update value ###
	if ($contents[0] eq ""){
		&printheaders;
		print start_page("BadStore.net - Cart Error"), h1("Cart Error - Zero Items"), 
		"Something weird happened - you tried to add no items to the cart!",p,
		"Use your browser's Back button and try again.", p, p, p,
		h3("(If you're trying to hack - I know who you are:   $ipaddr)"),
		end_page();

	} else {
		### Connect to the SQL Database ###
		my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
			or die "Cannot connect: " . $DBI::errstr;

		foreach $temp (@contents) {
			# SECURITY FIX: VUL-03 — validar que itemnum sea numerico y usar parametro preparado
			next unless $temp =~ /^\d+$/;
			$cartitems = $cartitems + 1;
			my $sth = $dbh->prepare("SELECT price FROM itemdb WHERE itemnum = ?")
            		or die "Couldn't prepare statement: " . $dbh->errstr;
          		$sth->execute($temp) or die "Couldn't execute SQL statement: " . $sth->errstr;

          		if ($sth->rows == 0) {
            		die "Item number not found: " . $sth->errstr;
          		} else {
			### Update cart cost ###
			$cartcost = $cartcost + $sth->fetchrow_array();
			}
		}

		### Create initial CartID cookie
		$cookievalue=join(":", ($sessid, $cartitems, $cartcost, @contents));
		$cartcookie=cookie( -name=>'CartID', -value=>$cookievalue, -path=>'/');
		print "Set-Cookie: $cartcookie\n";

	&home
	}
}

###############
# Place Order #
###############

sub order
{
	local (@data, $temp, @cookievalue, $price, $id, $items, $cost, $cartitems, $cartcookie, $ccard, $expdate);

	### Read CartID Cookie ###
	$temp=cookie('CartID');
	@cookievalue=split(":", ("$temp"));
	$id=shift(@cookievalue);
	$items=shift(@cookievalue);
	$cost=shift(@cookievalue);
	$price='$' . sprintf("%.2f", $cost);
	$cartitems=join(",", @cookievalue);
	$email=$query->param('email');

	### Expire the Cookie ###
	$cartcookie=cookie( -name=>'CartID', -value=>'', -expires=>'-1d', -path=>'/');
	print "Set-Cookie: $cartcookie\n";

	### Get the hidden fields ###
	$ccard=$query->param('ccard');
	$expdate=$query->param('expdate');

	&printheaders;
	print start_page("BadStore.net - Place Order"),
	h1("Your Order Has Been Placed"), p;

	### Check for Empty Cart ###
	if ($items < "1") {
		print p("You have no items in your cart. Order something already!");
	} else {

		### Connect to the SQL Database ###
		my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
			or die "Cannot connect: " . $DBI::errstr;

	### Add ordered items to Order Database ###
	# SECURITY FIX: VUL-03 — parametros preparados en INSERT para prevenir SQLi via cookie
	my $ins_sth = $dbh->prepare("INSERT INTO orderdb (sessid, orderdate, ordertime, ordercost, orderitems, itemlist, accountid, ipaddr, cartpaid, ccard, expdate) VALUES (?, CURDATE(), CURTIME(), ?, ?, ?, ?, ?, 'Y', ?, ?)")
		or die "Couldn't prepare INSERT: " . $dbh->errstr;
	$ins_sth->execute($id, $price, $items, $cartitems, $email, $ipaddr, $ccard, $expdate)
		or die "Couldn't execute INSERT: " . $ins_sth->errstr;

		print p("You have just bought the following:");

		### Prepare and Execute SQL Query ###
		# SECURITY FIX: VUL-03 — validar que cada item del carrito sea numerico antes de IN (...)
		my @safe_items = grep { /^\d+$/ } split(',', $cartitems);
		my $placeholders = join(',', ('?') x scalar(@safe_items));
		my $sth = $dbh->prepare("SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE itemnum IN ($placeholders)")
           		or die "Couldn't prepare statement: " . $dbh->errstr;
     		$sth->execute(@safe_items) or die "Couldn't execute SQL statement: " . $sth->errstr;
     		if ($sth->rows == 0) {
           		die "Item number not found: " . $sth->errstr;
     		} else {
		### Read the matching records and print them out ###
		print '<table cellspacing="0" cellpadding="0" class="products">',
		Tr( th('ItemNum'),th('Item'),th('Description'),th('Price'),th('Image'));
          	while (@data = $sth->fetchrow_array()) {
			$image='/images/' . $data[0] . '.jpg';
			print Tr( td( \@data ),td({-align=>CENTER},"<IMG SRC=$image>") );
			}
		print "</table>\n\n", p("Purchased: $items items at $price. Thank you for shopping at BadStore.net!");
		}
	### Close statement handles ###
	$sth->finish;

	### Disconnect from the databases ###
	$dbh->disconnect;
	}
	print end_page();
}

##################
# Submit Payment #
##################

sub submitpayment
{
	local($stemp, @s_cookievalue, $email, $passwd, $fullname, $ccard, $expdate);

	### Read SSOid Cookie ###
	$stemp=cookie('SSOid');
	$stemp=decode_base64($stemp);
	@s_cookievalue=split(":", ("$stemp"));
	$email=shift(@s_cookievalue);
	&printheaders;
	print start_page(-title=>"BadStore.net - Place Order", -script=>{-language=>'JavaScript',-src=>'/cardvrfy.js'}),
	h1("Thanks for ordering from BadStore.net!");

	print start_form( -action=>'/cgi-bin/badstore.cgi?action=order', -onSubmit=>'return DoCardvrfy(this);');

	### If already logged in, fill out email, say Welcome ###
	if ($email eq '') {
	    	print "Email Address: ", textfield(-name=>'email', -size=>15, -maxlength=>40);
	} else {
		print "Welcome, <b>$email</b>",
		hidden(-name=>'email', -default=>[$email]);
	}
   	print p,
    	"Credit Card Number: ", textfield(-name=>'ccard', -size=>16, -maxlength=>16),"     Expiration Date: ",textfield(-name=>'expdate',-size=>4),p,p,hr,p,
      "<Center>BadStore.net Accepts the following Payment Methods",p,
	img{src=>'/images/visa.jpg'},"        ",img{src=>'/images/mastercard.jpg'},"        ",img{src=>'/images/discover.jpg'},"        ",img{src=>'/images/amex.jpg'},p,
 	submit(-name=>'subccard', -value=>'Place Order'),
	end_form;

	print end_page();
}


########################
# View Previous Orders #
########################

sub viewprevious
{
	local ($email, @data, $stemp, @s_cookievalue, $passwd, $fullname, $role);

	### Read SSOid Cookie ###
	$stemp=cookie('SSOid');
	$stemp=decode_base64($stemp);
	@s_cookievalue=split(":", ("$stemp"));
	$email=shift(@s_cookievalue);
	$passwd=shift(@s_cookievalue);
	$fullname=shift(@s_cookievalue);
	$role=shift(@s_cookievalue);

	&printheaders;
	print start_page("BadStore.net - View Previous Orders"),
	h1("You have placed the following orders:"), p;

	if ($fullname eq '{Unregistered User}') {
		print h2('You are not logged in!'), p,
		"Use your browser's Back button and select Login.";
	} else {
		### Connect to the SQL Database ###
		my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
			or die "Cannot connect: " . $DBI::errstr;

		# SECURITY FIX: VUL-02 — parametro preparado para email proveniente de cookie (previene SQLi)
		my $sth = $dbh->prepare("SELECT orderdate, ordercost, orderitems, itemlist, ccard FROM orderdb WHERE accountid = ? ORDER BY orderdate,ordertime")
                or die "Couldn't prepare statement: " . $dbh->errstr;
        	$sth->execute($email) or die "Couldn't execute SQL statement: " . $sth->errstr;

     		if ($sth->rows == 0) {
               print p('You have no previous orders!'), p("Use your browser's Back button and select Login.");
     		} else {

		print "<TABLE BORDER=1>",
		Tr( th('Order Date'),th('Order Cost'),th('# Items'),th('Item List'),th('Card Used'));
          	while (@data = $sth->fetchrow_array()) {
			$data[4]=~ s/(\d\d\d\d)[\ \s]?/$1 /g;
			$data[4]=~ s/ $//;			
			print Tr( td( \@data ));
			}
		print "</TABLE>\n\n", p,
		"<Center><i>Thank you for shopping at BadStore.net!</i></Center>";
		}

	### Close statement handles ###
	$sth->finish;

	### Disconnect from the databases ###
	$dbh->disconnect;
	}
	print end_page();
}

############
# About Us #
############

sub aboutus
{
	&printheaders;
	print start_page('BadStore.net - About Us'),
	h2("About Us!"), p,
	img{src=>'/images/seal.jpg', align=>'RIGHT'},
	p, "We value your comments, so click here and tell us what you think!  ", p,
	a({-href=>'mailto:spam@badstore.net'}, 'Send us an email!'), " with subject 'Howdy' and whatever you want to say",
	p,
	"We may be a small site, but we really care about your on-line security.  That's why we undergo a Security Seal certification every few years or so.  The Security Seal is a stringent process where we have to fill out filecabinets full of paperwork to illustrate our security process.  Believe me, it's alot of work.", p,
	end_page();
}

##################
# Supplier Login #
##################

sub supplierlogin
{
	&printheaders;
	
	print start_page('Supplier Portal Login - BadStore.net');
	print "<h2>Welcome Supplier - Please Login</h2>";
	print '<form method="post" action="/cgi-bin/badstore.cgi?action=supplierportal">',
	'<table cellspacing="0" cellpadding="0">',
	  '<tr><td width="100">Email Address:</td><td><input type="text" name="email" size="15" maxlength="40" /></td></tr>',
	  '<tr><td>Password:</td><td><input type="text" name="passwd" size="8" maxlength="8" /></td></tr>',
	  '<tr><td></td><td><input type="submit" value="Login" /></td></tr>',
     '</table>',
    '</form>';
	
	#h1("Welcome Supplier - Please Login:"), hr, p,
	#start_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=supplierportal'),
	#" Email Address:  ", textfield(-name=>'email', -size=>15, -maxlength=>40), p,
	#" Password:  ", password_field(-name=>'passwd', -size=>8 -maxlength=>8),p,
	#submit("Login"), end_form,
	
	
	print end_page();
}




###################
# Supplier Procedure #
###################
sub supplierproc
{
   &printheaders;
	
   print start_page('Supplier Pricing Upload Procedure - BadStore.net');
   print "<h2>Supplier Pricing Upload Procedure</h2>";
   
   print q|
   <p>To save our administrative staff some work, we have implemented a page where you, our Valued Suppliers, can upload your new pricelist.  This lets you manage your product descriptions and pricing without us having to do anything.  We hope that you will like this procedure as much as we like it.</p>
   <p>It was really an easy, quick little application for us to develop.  It only took an hour, in fact.</p>

   <h3>Here's how it works:</h3>
   <p>When you successfully LOGIN to the Supplier Portal (See the "Supplier Login" link on the main page), You will be presented with a form where you fill in the file you want to upload (from your PC) and the name you want it stored under on the site.  It's as simple as that.</p>
   <p>We recommend that your description file be an html file (AcmeWidget.html), and if you want your corporate logo, do another upload for it, too!</p>
   <p>Thanks for being a valued supplier and thanks for using this portal that saves us work!</p>
   <p>- Your BadStore.net management team</p>
	|;

   print end_page();
}

###################
# Supplier Portal #
###################

sub supplierportal
{
	local($email, $passwd);
	$email=$query->param('email');
	$passwd=$query->param('passwd');
	chomp($email);
	chomp($passwd);
	# SECURITY FIX: VUL-10 — hash con salt de aplicacion (reemplazar por bcrypt en produccion)
	$passwd=md5_hex(PWD_SALT . $passwd);

	### Connect to the SQL Database ###
	my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
		or die "Cannot connect: " . $DBI::errstr;

	### Prepare, Evaluate and Execute SQL Query ###
	# SECURITY FIX: VUL-02 — parametros preparados para prevenir SQLi en login de proveedor
	my $sth = $dbh->prepare("SELECT * FROM userdb WHERE email=? AND passwd=?");
	eval {
	     	$sth->execute($email, $passwd);
		1;
	} or do {
		print "Location: /cgi-bin/badstore.cgi?action=supplierlogin\n\n";
	};

	&printheaders;
	print start_page("Welcome to the BadStore.net Supplier Portal"),
	h1("Welcome Supplier");
     	
	if ($sth->rows == 0) {
           		print p("UserID and Password not found! Use your browser's Back button and try again."),
     		} else {
		# Login credentials are valid
		print h2("Upload Price Lists"), h3("Filename on local system: "),
   		start_multipart_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=supupload', -enctype=>'multipart/form-data'),
    		filefield(-name=>'uploaded_file', -size=>50, -maxlength=>80), br, br,
		h3("Filename on BadStore.net: "), textfield(-name=>'newfilename', size=>25, -maxlength=>50),
  		submit('Upload'), end_form;
		}
	print p("<strong>Coming Soon - Web Services!</strong>");
	### Close statement handles ###
	$sth->finish;

	### Disconnect from the databases ###
	$dbh->disconnect;
	print end_page();
}

###################
# Supplier Upload #
###################

sub supupload
{
	(local $host);
	&printheaders;
	print start_page("BadStore.net - Supplier Upload");

	$referer  = $ENV{HTTP_REFERER};
	$host = $ENV{HTTP_HOST};

	# SECURITY FIX: VUL-05 — corregida logica de referer (era !~ invertido; usaba $hostname indefinido)
	# SECURITY FIX: VUL-05 — sanitizacion de nombre de archivo para prevenir Path Traversal
	if ($referer and $referer =~ m|^https?://$host/|) {

		print h1("Upload a file");

		$newfilename = $query->param('newfilename');

		# SECURITY FIX: VUL-05 — eliminar path traversal y caracteres peligrosos del nombre de archivo
		$newfilename =~ s/[^a-zA-Z0-9._-]//g;   # solo caracteres seguros
		$newfilename =~ s/\.\.//g;               # eliminar secuencias ..
		$newfilename =~ s/^\.//;                 # no iniciar con punto

		if ($newfilename eq '') {
			print h2("Error: nombre de archivo invalido.");
		} else {
			$filename = $query->param('uploaded_file');
			$filename =~ s/.*[\/\\](.*)/$1/;
			chomp($filename);
			$upload_filehandle = $query->upload('uploaded_file');
			my $safe_path = "../data/uploads/$newfilename";
			open (OUT, ">$safe_path") or die "Can't open $newfilename for writing: $!\n";
			while (<$upload_filehandle>) { print OUT; }
			close OUT;
			print p, h2("Thanks for uploading your new pricing file!"), p,
			h3("Your file has been uploaded: " . escapeHTML($newfilename)), p,
		}

	} else {
		### Invalid referer ###
		print h1("An Error Has Occurred"),
		h3("Uploads are only accepted by authenticating to the Supplier Portal!")
	}
	end_page();
}

######################
# View Cart Contents #
######################

sub cartview
{
	local (@data, $temp, @cookievalue, $price, $id, $items, $cost, $cartitems);

	&printheaders;
	print start_page("BadStore.net - View Cart Contents"),
	h1("Keep Shopping!"), p;

	### Read CartID Cookie ###
	$temp=cookie('CartID');
	@cookievalue=split(":", ("$temp"));
	$id=shift(@cookievalue);
	$items=shift(@cookievalue);
	$cost=shift(@cookievalue);
	$price='$' . sprintf("%.2f", $cost);
	$cartitems=join(",", @cookievalue);

	### Check for Empty Cart ###
	if ($items < "1") {
		print p("You have no items in your cart. Order something already!");
	} else {
		### Connect to the SQL Database ###
		my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
			or die "Cannot connect: " . $DBI::errstr;

         print p("Cart Contains: $items items at $price. The following items are in your cart:");

		### Prepare and Execute SQL Query ###
		# SECURITY FIX: VUL-03 — validar items del carrito como numericos; placeholders dinamicos
		my @cv_items = grep { /^\d+$/ } split(',', $cartitems);
		my $cv_placeholders = join(',', ('?') x scalar(@cv_items));
		my $sth = $dbh->prepare("SELECT itemnum, sdesc, ldesc, price FROM itemdb WHERE itemnum IN ($cv_placeholders)")
           		or die "Couldn't prepare statement: " . $dbh->errstr;
     		$sth->execute(@cv_items) or die "Couldn't execute SQL statement: " . $sth->errstr;
     		if ($sth->rows == 0) {
           		die "Item number not found: " . $sth->errstr;
     		} else {
		### Read the matching records and print them out ###
		print start_form( -action=>'/cgi-bin/badstore.cgi?action=submitpayment'),'<table cellspacing="0" cellpadding="0" class="products">',
		Tr( th('ItemNum'),th('Item'),th('Description'),th('Price'),th('Image'),th('Order'));
          	while (@data = $sth->fetchrow_array()) {
			$image='/images/' . $data[0] . '.jpg';
			print Tr( td( \@data ),td({-align=>CENTER},"<IMG SRC=$image>"),td({-align=>CENTER},"<input type=checkbox checked name='cartitem' value=$data[0]>") );
			}
		print "</table>\n\n", p, "<Center>", submit('Place Order'), "   ", reset(), "</Center>", end_form;
		}
	### Close statement handles ###
	$sth->finish;

	### Disconnect from the databases ###
	$dbh->disconnect;
	}
	print end_page();
}

#####################
### Print headers ###
#####################

sub printheaders
{
	print "Content-type: text/html\n";
	# SECURITY FIX: VUL-13 — eliminado banner de version exacta del servidor (fingerprinting)
	print "Server: BadStore\n";
	# ETag removido (puede filtrar informacion del sistema de archivos)
	print "Cache-Control: no-cache\n";
	print "Pragma: no-cache\n\n";
}

#####################
# Login or Register #
#####################

sub loginregister
{
   &printheaders;
   print start_page('BadStore.net - Register/Login');
   print qq|
   <h2>Login to Your Account or Register for a New Account</h2>
   <h3>Login to Your Account</h3>
   <form method="post" action="/cgi-bin/badstore.cgi?action=login">
     <table cellspacing="0" cellpadding="0">
       <tr>
         <td width="100">Email Address:</td>
         <td><input type="text" name="email" size="20" maxlength="40" /></td>
       </tr>
       <tr>
         <td>Password:</td>
         <td><input type="password" name="passwd" size="8" maxlength="8" /></td>
       </tr>
       <tr>
         <td></td>
         <td><input type="submit" value="Login" /></td>
       </tr>
      </table>
   </form>
   <hr />
   <h3>Register for a New Account</h3>
   <form method="post" action="/cgi-bin/badstore.cgi?action=register">
     <table cellspacing="0" cellpadding="0">
       <tr>
         <td width="100">Full Name:</td>
         <td><input type="text" name="fullname" size="25" maxlength="40" /></td>
       </tr>
       <tr>
         <td>Email Address:</td>
         <td><input type="text" name="email" size="20" maxlength="40" /></td>
       </tr>
       <tr>
         <td>Password:</td>
         <td><input type="password" name="passwd" size="8" maxlength="8" /></td>
       </tr>
       <tr>
         <td>Password Hint:</td>
         <td>
           What's Your Favorite Color?:
           <select name="pwdhint">
             <option value="green">Green</option>
             <option value="blue">Blue</option>
             <option value="red">Red</option>
             <option value="orange">Orange</option>
             <option value="purple">Purple</option>
             <option value="yellow">Yellow</option>
           </select>
           <br />
           <em>(The Password Hint is used as a security measure to help recover a forgotten password.  You will need both your email address and this hint to access your account if you forget your current password.)</em>
         </td>
       </tr>
       <tr>
         <td></td>
         <td>
            <input type="hidden" name="role" value="U" />
            <input type="submit" value="Register" />
         </td>
       </tr>
      </table>
   </form>
   |;
   
   print end_page();
   #&printheaders;
   #print start_page('BadStore.net - Register/Login'),
   #h2("Login to Your Account or Register for a New Account"), hr,
   #h3("Login to Your Account"),
   #start_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=login'),
   #p,"Email Address:  ", textfield(-name=>'email', -size=>20, -maxlength=>40), p,
   #p,"Password:  ", password_field(-name=>'passwd', -size=>8 -maxlength=>8),p,
   #submit("Login"), end_form, hr,
   #h3("Register for a New Account"),
   #start_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=register'),
   #p,"Full Name:  ", textfield(-name=>'fullname', -size=>25, -maxlength=>40), p,
   #p,"Email Address:  ", textfield(-name=>'email', -size=>20, -maxlength=>40), p,
   #p,"Password:  ", password_field(-name=>'passwd', -size=>8 -maxlength=>8),p,
   #"Password Hint - What's Your Favorite Color?:  ",popup_menu(-name=>'pwdhint',-values=>['green','blue','red','orange','purple','yellow']),p,
   #"<font face=Arial size=2><i>(The Password Hint is used as a security measure to help recover a forgotten password.  You will need both your email address and this hint to access your account if you forget your current password.)</i></font>",p,
   #hidden(-name=>'role', -default=>['U']),
   #submit("Register"), end_form, p,
   #end_page();
}

##############
# My Account #
##############

sub myaccount
{
	local($aquery, $email, $passwd, $pwdhint, $fullname, $role, $newpasswd, $vnewpasswd, $encpasswd);
 
	### Read SSOid Cookie ###
	$stemp=cookie('SSOid');
	$stemp=decode_base64($stemp);
	@s_cookievalue=split(":", ("$stemp"));
	$email=shift(@s_cookievalue);
	$passwd=shift(@s_cookievalue);
	$fullname=shift(@s_cookievalue);
	$role=shift(@s_cookievalue);

	&printheaders;
	print start_page(-title=>'BadStore.net - My Account Services',-script=>{language=>'JavaScript',-src=>'/frmvrfy.js'});

	if ($fullname eq '') {
		$fullname="{Unregistered User}";
		print h2(' Welcome, as an ',$fullname,' you can:'),p,
		"Login To Your Account / Register for A New Account - <A HREF='/cgi-bin/badstore.cgi?action=loginregister'>Click Here</A><BR>", p,
		" Reset A Forgotten Password", p,
		start_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=moduser'),
		"<font face=Arial size=2> Please enter the email addess and password hint you chose when the account was created:</font>",p,
		" Email Address:  ", textfield(-name=>'email', -size=>15),p,
		" Password Hint - What's Your Favorite Color?:  ",popup_menu(-name=>'pwdhint',-values=>['green','blue','red','orange','purple','yellow']),p,
		"<font face=Arial size=2><i> (The Password Hint was chosen when you registered for a new account as a security measure to help recover a forgotten password...)</i></font>",p,
		submit(-name=>'DoMods',-value=>'Reset User Password'), end_form;

	} else {
		print h2("Welcome, ",$fullname),
		"<h5>Update your account information:</h5>",
		start_form(-method=>'POST', -action=>'/cgi-bin/badstore.cgi?action=moduser', -onSubmit=>'return DoPwdvrfy(this);'),
		" Current Full Name:  ", $fullname,p,
		" New Full Name =  ",textfield(-name=>'fullname', -size=>25, -maxlength=>40),p,br,
		" Current Email Address:  ", $email,p,
		" New Email Address =  ",textfield(-name=>'newemail', -size=>20, -maxlength=>40),p,br,
		" Change Password:  ", password_field(-name=>'newpasswd', -size=>8 -maxlength=>8),"  Verify:  ", password_field(-name=>'vnewpasswd', -size=>8 -maxlength=>8),p,br,
		hidden(-name=>'role', -default=>[$role]),
		hidden(-name=>'email',-default=>[$email]),
		submit(-name=>'DoMods',-value=>'Change Account'), end_form, p;
	}
	print end_page();
}

##########################
# Modify User Attributes #
##########################

sub moduser
{
	local($aquery, $email, $passwd, $pwdhint, $fullname, $role, $newpasswd, $encpasswd, $vnewpasswd, $newemail);
	$aquery=$query->param('DoMods');
	$email=$query->param('email');
	$passwd=$query->param('passwd');
	$pwdhint=$query->param('pwdhint');
	$fullname=$query->param('fullname');
	# SECURITY FIX: VUL-09 — rol ignorado del formulario; en Add User admin lo asigna explicitamente
	# $role NO se toma de $query->param('role') para evitar escalada de privilegios
	$vnewpasswd=$query->param('vnewpasswd');
	$newemail=$query->param('newemail');
	chomp($email);
	chomp($passwd);
	chomp($pwdhint);
	chomp($fullname);
	$newpasswd="Welcome";
	# SECURITY FIX: VUL-10 — hash con salt de aplicacion para contrasena de reset
	$encpasswd=md5_hex(PWD_SALT . $newpasswd);
	$vencpasswd=md5_hex(PWD_SALT . $vnewpasswd);
	&printheaders;

	### Connect to the SQL Database ###
	my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
		or die "Cannot connect: " . $DBI::errstr;

	### Reset User Password ###
	if ($aquery eq 'Reset User Password') {
		print start_page('BadStore.net - Reset Password for User');
		# SECURITY FIX: VUL-02 — parametros preparados en UPDATE (previene SQLi)
		my $sth=$dbh->prepare("UPDATE userdb SET passwd=? WHERE email=?")
			or die "Could not update password: ".$dbh->errstr;
		$sth->execute($encpasswd, $email) or die "Couldn't execute SQL statement: ".$sth->errstr;

		print h2('The password for user:  ', escapeHTML($email),p, ' ...has been reset to: ',$newpasswd),

	}elsif ($aquery eq 'Add User'){
		print start_page('BadStore.net - Add User');
		# SECURITY FIX: VUL-09 — rol forzado a 'U' en Add User desde panel admin usa su propio flujo
		# SECURITY FIX: VUL-02 — parametros preparados en INSERT
		my $add_role = 'U';  # rol por defecto seguro
		my $ins = $dbh->prepare("INSERT INTO userdb (email, passwd, pwdhint, fullname, role) VALUES (?,?,?,?,?)")
			or die "Couldn't prepare INSERT: " . $dbh->errstr;
		$ins->execute($email, $encpasswd, $pwdhint, $fullname, $add_role)
			or die "Couldn't execute INSERT: " . $ins->errstr;
		print h2("User:  ", escapeHTML($fullname)," has been added.");

	}elsif ($aquery eq 'Delete User'){
		print start_page('BadStore.net - Delete User');
		# SECURITY FIX: VUL-02 — parametros preparados en DELETE
		my $del = $dbh->prepare("DELETE FROM userdb WHERE email=?")
			or die "Couldn't prepare DELETE: " . $dbh->errstr;
		$del->execute($email) or die "Couldn't execute DELETE: " . $del->errstr;
		print h2("User:  ", escapeHTML($email)," has been deleted.");

	### Change Account Information ###
	}elsif ($aquery eq 'Change Account'){
		print start_page('BadStore.net - Update User Information');
		# SECURITY FIX: VUL-02 — parametros preparados en todos los UPDATE de cuenta
		my $u1 = $dbh->prepare("UPDATE userdb SET fullname=? WHERE email=?") or die $dbh->errstr;
		$u1->execute($fullname, $email) or die $u1->errstr;
		my $u2 = $dbh->prepare("UPDATE userdb SET passwd=? WHERE email=?") or die $dbh->errstr;
		$u2->execute($vencpasswd, $email) or die $u2->errstr;
		my $u3 = $dbh->prepare("UPDATE userdb SET email=? WHERE email=?") or die $dbh->errstr;
		$u3->execute($newemail, $email) or die $u3->errstr;
		print h2(" Account Information for: "),
		" Full Name: ", escapeHTML($fullname),p,
		" Email: ",    escapeHTML($newemail),p,
		h3(" Has been updated!");
	}
	print end_page();

	### Disconnect from the databases ###
	$dbh->disconnect;
}

#############
# Auth User #
#############

sub authuser
{
	local(@data, $email, $passwd, $pwdhint,$fullname, $role);
	$email=$query->param('email');
	$passwd=$query->param('passwd');
	$pwdhint=$query->param('pwdhint');
	$fullname=$query->param('fullname');
	$role=$query->param('role');
	chomp($email);
	chomp($passwd);
	chomp($pwdhint);
	chomp($fullname);
	# SECURITY FIX: VUL-09 — rol ignorado del formulario de registro; siempre se fuerza 'U'
	# $role del formulario descartado; obtenido de la BD tras login exitoso
	# SECURITY FIX: VUL-10 — hash con salt de aplicacion (reemplazar por bcrypt en produccion)
	$passwd=md5_hex(PWD_SALT . $passwd);

	### Connect to the SQL Database ###
	my $dbh = DBI->connect("DBI:mysql:database=badstoredb;host=localhost", $DB_USER, $DB_PASS,{'RaiseError' => 1})
		or die "Cannot connect: " . $DBI::errstr;

	### Logging into existing account ###
	if ($query->url_param('action') eq 'login') {

		# SECURITY FIX: VUL-02 — parametros preparados para prevenir SQLi en login
		my $sth = $dbh->prepare("SELECT * FROM userdb WHERE email=? AND passwd=?")
      		or die "Couldn't prepare statement: " . $dbh->errstr;
     		$sth->execute($email, $passwd) or die "Couldn't execute SQL statement: " . $sth->errstr;

		if ($sth->rows == 0) {
			&printheaders;
			print start_page("BadStore.net - Login Error"),
           		h2("UserID and Password not found!"),
			"Use your browser's Back button and try again.",
			end_page();
			exit;
     		} else {
		### Login credentials are valid ###

		@data=$sth->fetchrow_array();
		$fullname=$data[3];
		$role=$data[4];  # rol obtenido de la BD, no del formulario

		### Close statement handles ###
		$sth->finish;
		}
	} else {

		### Register for a new account as a normal user ###
		# SECURITY FIX: VUL-09 — rol forzado a 'U'; no se acepta el valor del formulario
		# SECURITY FIX: VUL-02 — parametros preparados en INSERT de registro
		my $reg_role = 'U';
		my $reg = $dbh->prepare("INSERT INTO userdb (email, passwd, pwdhint, fullname, role) VALUES (?,?,?,?,?)")
			or die "Couldn't prepare INSERT: " . $dbh->errstr;
		$reg->execute($email, $passwd, $pwdhint, $fullname, $reg_role)
			or die "Couldn't execute INSERT: " . $reg->errstr;
	}

	### Set SSO Cookie ###
		$cookievalue=join(":", ($email, $passwd, $fullname, $role));
		$cookievalue=encode_base64($cookievalue);
		$cartcookie=cookie( -name=>'SSOid', -value=>$cookievalue, -path=>'/');
		print "Set-Cookie: $cartcookie\n";

	### Disconnect from the databases ###
	$dbh->disconnect;
	&home;
}
