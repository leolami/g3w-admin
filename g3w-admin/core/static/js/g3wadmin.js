/**
 * Created by walter on 18/02/16.
 */

/**
 * Use of https://github.com/sinkswim/javascript-style-guide for javascript coding style.
 */

var $m;

$(document).ready(function(){
    $('#bt_test').click(function(){
        ga.widget.deleteItem($(this));
    });

    ga.bootstrap();
});