$(document).ready(function() {
  $(':submit, :reset').each(function(index, input) {
    var button = $(input);
    var id = button.attr('id');
    var name = button.attr('name');
    var type = button.attr('type');
    var value = button.attr('value');
    var link = $('<a>'+value+'</a>');
    if (id) {
      link.attr('href', '#'+id);
    } else if (name) {
      link.attr('href', '#'+name);
    } else if (type) {
      link.attr('href', '#'+type);
    } else {
      link.attr('href', '#button');
    }
    link.attr('title', value).attr('class', button.attr('class')).data('button', button).on('click', function(event) {
      $(this).data('button').click();
    });
    button.hide().after(link);
  });
});