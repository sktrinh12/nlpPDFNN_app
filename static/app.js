function filesize(elem){
  var fz = elem.files[0].size;
  console.log(fz);
  document.cookie = `filesize=${fz}`;
};

function clear_fz(){ //set the filesize back to 0 again
  console.log('clear');
  document.cookie = "filesize=0";
};

function close_btn(){ //close the flash message
  $('#flash-msg').html("");
  clear_fz();
};

var fileInputDiv = document.querySelector('.custom-file-input');
if (fileInputDiv !== null) {
  fileInputDiv.addEventListener('change',function(e){ //show filename in the input
    var fileName = document.getElementById("pdf_up").files[0].name;
    var nextSibling = e.target.nextElementSibling
    nextSibling.innerText = fileName
  });
};

// loader appears in between pages and links
window.addEventListener("load", function () {
    const loaderWrap = document.querySelector(".loader-wrapper");
    loaderWrap.className += " hidden";
});

// loader appears after click button and waiting for flask to finish
function loading() {
    document.querySelector(".loader-wrapper").className = "loader-wrapper";
    setTimeout(clear_fz, 12000);
};

// switch tabs on navbar triggering active tab
function switch_tabs(navbar) {
	if (navbar === $("#email-navbar")[0]) {
		navbar.className = "nav-link active";
		document.getElementById("email-navbar").className = "nav-link";
	} else {
		navbar.className = "nav-link active";
		document.getElementById("email-navbar").className = "nav-link";
	};
};

// use of onbeforeunload to detect refresh
function loader_refresh() {
  loading();
  console.log('refresh button clicked');
};
