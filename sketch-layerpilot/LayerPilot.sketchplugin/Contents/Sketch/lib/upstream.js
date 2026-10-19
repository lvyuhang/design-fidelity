// Adapted from Ashung/Automate-Sketch, Export/Quick_Export.js.
// Revision 4cc9ccf72052dc39f976ffdbc7aca3df2ada5738.
// Copyright (c) 2022 Ashung Hung. MIT; see Contents/Resources/LICENSE.
// Kept independent of upstream's native export APIs and analytics modules.
function nameParts(name) {
  var regSlash = /\s?[\/\\]+\s?/;
  return name.trim().split(regSlash).filter(function(item) {
    return item !== '';
  });
}
function formatNameUnderLine(name) {
  return name.trim().replace(/\s+/g, '_').replace(/-/g, '_').toLowerCase();
}
exports.nameParts = nameParts;
exports.formatNameUnderLine = formatNameUnderLine;
