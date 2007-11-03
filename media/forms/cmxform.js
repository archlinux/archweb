if( document.addEventListener ) document.addEventListener( 'DOMContentLoaded', cmxform, false );

function cmxform(){
  // Hide forms
  $( 'form.cmxform' ).hide().end();
  
  // Processing
  $( 'form.cmxform' ).find( 'li/label' ).not( '.nocmx' ).each( function( i ){
    var labelContent = this.innerHTML;
    var labelWidth = document.defaultView.getComputedStyle( this, '' ).getPropertyValue( 'width' );
    var labelSpan = document.createElement( 'span' );
        labelSpan.style.display = 'block';
        labelSpan.style.width = labelWidth;
        labelSpan.innerHTML = labelContent;
    this.style.display = '-moz-inline-box';
    this.innerHTML = null;
    this.appendChild( labelSpan );
  } ).end();
  
  // Show forms
  $( 'form.cmxform' ).show().end();
}