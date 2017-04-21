var fgs = ['blue', 'red', 'green', 'yellow', 'pink', 'cyan', 'white', 'black'];
var bgs = ['yellow', 'green', 'white', 'purple', 'black', 'green', 'red', 'blue', 'black'];
var timeout = 150;
var pos = 0;
var snowmen, snowflakes;

function init_snowman() {
  snowmen = document.getElementById('snowmen');
  snowflakes = document.getElementById('snowflakes');
  animate_snowman();
}

function animate_snowman() {
  pos = (pos + 11) % 200;
  document.body.style.background = bgs[Math.floor(Math.random() * bgs.length)];
  snowmen.style.color = fgs[Math.floor(Math.random() * fgs.length)];
  snowflakes.style.top = -200 + pos + "pt";
  snowflakes.style.left = Math.random() * 30 - 15;
  setTimeout(animate_snowman, timeout);
}
