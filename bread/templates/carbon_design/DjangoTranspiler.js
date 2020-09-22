"use strict";

var _interopRequireWildcard = require("@babel/runtime/helpers/interopRequireWildcard");

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");

exports.__esModule = true;
exports.DjangoTranspiler = void 0;

var _handlebars = _interopRequireDefault(require("handlebars"));

var _Context = _interopRequireWildcard(require("./Context"));

var DjangoTranspiler =
/*#__PURE__*/
function () {
  function DjangoTranspiler(input, context, depth) {
    if (depth === void 0) {
      depth = 0;
    }

    Object.defineProperty(this, "buffer", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    Object.defineProperty(this, "parsed", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    Object.defineProperty(this, "context", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    Object.defineProperty(this, "depth", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    this.buffer = [];
    this.context = context || new _Context.default();
    this.depth = depth;

    if (input) {
      this.parsed = _handlebars.default.parse(input);
      this.parseProgram(this.parsed);
    }
  }

  var _proto = DjangoTranspiler.prototype;

  _proto.parseProgram = function parseProgram(program, isConditionalInInverse) {
    var _this = this;

    if (isConditionalInInverse === void 0) {
      isConditionalInInverse = false;
    }

    program.body.forEach(function (statement) {
      switch (statement.type) {
        case 'ContentStatement':
          _this.buffer.push(statement.original);

          break;

        case 'MustacheStatement':
          var path = statement.path;
          var escaped = statement.escaped ? '' : '|safe';
          var variable;
          
          if (statement.path.original === 'carbon-icon') {
              var icon = '{% carbon_icon "' + statement.params[0].value + '"';
              if(typeof (statement.hash) !== "undefined" && typeof (statement.hash.pairs) !== "undefined") {
                  for(let pair of statement.hash.pairs) {
                      var value = "?";
                      if(pair.value.type == "StringLiteral") {
                          value = pair.value.value;
                      }
                      else if(pair.value.type == 'SubExpression' && pair.value.path.original === "add") {
                          if(pair.value.params[0].type === 'PathExpression' && pair.value.params[1].type == 'StringLiteral') {
                              value = 'bx' + pair.value.params[1].value;
                          } else if(pair.value.params[0].type === 'PathExpression' && pair.value.params[1].type == 'SubExpression') {
                              value = 'bx--{{ variant }}' + pair.value.params[1].params[1].params[1].value;
                          } else if(pair.value.params[0].type === 'SubExpression' && pair.value.params[1].type == 'SubExpression') {
                              value = ''
                              function find_classes(elem) {
                                  var ret = [];
                                  if('params' in elem) {
                                      for(let p of elem.params) {
                                          if(p.type === 'StringLiteral' && p.value !== ' ') {
                                              ret.push('bx' + p.value);
                                          } else if ('params' in p) {
                                              ret.push(...find_classes(p))
                                          }
                                      }
                                  }
                                  return ret
                              }
                              value = find_classes(pair.value).join(' ');
                          }
                      }
                      icon += ' ' + pair.key.replace('-', '_') + '="' + value + '"'
                  }
              }
              _this.buffer.push(icon + ' %}');
              break;
          }

          if (path.original === '@index') {
            variable = 'forloop.counter0';
          } else {
            variable = _this.context.getScopedVariable(path);
          }

          if (path.type === 'PathExpression') {
            _this.buffer.push("{{ " + variable + escaped + " }}");
          } else if (path.type === 'Literal') {
            throw new Error('not implemented');
          }

          break;

        case 'CommentStatement':
          _this.buffer.push("{#" + statement.value + "#}");

          break;

        case 'BlockStatement':
          var type = statement.path.original;

          switch (type) {
            case 'if':
              {
                var condition = statement.params[0];
                var scopedCondition;

                if (condition.type === 'SubExpression') {
                  if (condition.path.original === 'condition') {
                    scopedCondition = condition.params.map(function (param) {
                      if (param.type === 'PathExpression') {
                        return _this.context.getScopedVariable(param);
                      }

                      return param.value;
                    }).join(' ');
                  }
                } else {
                  scopedCondition = _this.context.getScopedVariable(condition);
                } // use `else if` instead of else when this is the only if statement in an else block


                _this.buffer.push("{% " + (isConditionalInInverse ? 'el' : '') + "if " + scopedCondition + " %}");

                var t = new DjangoTranspiler(null, _this.context, _this.depth);

                _this.buffer.push(t.parseProgram(statement.program).toString());

                if (statement.inverse) {
                  // else section
                  var isInverseOnlyConditional = DjangoTranspiler.isOnlyCondition(statement.inverse);

                  var _t = new DjangoTranspiler(null, _this.context, _this.depth);

                  _t.parseProgram(statement.inverse, isInverseOnlyConditional); // child will render a `else if`


                  if (!isInverseOnlyConditional) {
                    _this.buffer.push("{% else %}");
                  }

                  _this.buffer.push(_t.toString());
                } // parent will close this


                if (!isConditionalInInverse) {
                  _this.buffer.push("{% endif %}");
                }

                break;
              }

            case 'unless':
              {
                var condition = statement.params[0];
                var scopedCondition;

                if (condition.type === 'SubExpression') {
                  if (condition.path.original === 'condition') {
                    scopedCondition = condition.params.map(function (param) {
                      if (param.type === 'PathExpression') {
                        return _this.context.getScopedVariable(param);
                      }

                      return param.value;
                    }).join(' ');
                  }
                } else {
                  scopedCondition = _this.context.getScopedVariable(condition);
                } // use `else if` instead of else when this is the only if statement in an else block

                _this.buffer.push("{% if not " + scopedCondition + " %}");
                var t = new DjangoTranspiler(null, _this.context, _this.depth);
                _this.buffer.push(t.parseProgram(statement.program).toString());
                _this.buffer.push("{% endif %}");
                break;
              }

            case 'eq':
            case 'is':
              {
                var v1 = _this.context.getScopedVariable(statement.params[0]);
                var v2 = statement.params[1];

                _this.buffer.push("{% if " + v1 + " == " + v2 + " %}");
                var t = new DjangoTranspiler(null, _this.context, _this.depth);
                _this.buffer.push(t.parseProgram(statement.program).toString());
                _this.buffer.push("{% endif %}");
                break;
              }
            case 'with':
              {
                  // assumes only lookup is used in the with statement........
                childContext = _this.context.createChildContext(statement.program.blockParams);
                var v1 = _this.context.getScopedVariable(statement.params[0].params[0]);
                var v2 = _this.context.getScopedVariable(statement.params[0].params[1]);
                var t = new DjangoTranspiler(null, childContext, _this.depth);
                _this.buffer.push("{% with " + statement.program.blockParams[0] + "=" + v1 + "|lookup:" + v2 + " %}");
                _this.buffer.push(t.parseProgram(statement.program).toString());
                _this.buffer.push("{% endwith  %}");
                break;
              }

            case 'each':
              {
                var _condition = _this.context.getScopedVariable(statement.params[0]);

                var childContext;

                if (statement.program.blockParams) {
                  // {{#each foo as |key, value|}
                  var blockParams = statement.program.blockParams;
                  childContext = _this.context.createChildContext(blockParams); // {{#each foo as |k, v|} => has 2 variable in the same context, k and v

                  if (blockParams.length === 2) {
                    childContext.getCurrentScope().iterateAsObject();
                  }
                } else {
                  // {{#each foo}}
                  childContext = _this.context.createChildContext([_condition.split('.').pop() + "_i"]);
                }

                var _t2 = new DjangoTranspiler(null, childContext, _this.depth + 1);

                _t2.parseProgram(statement.program);

                var childScope = childContext.getCurrentScope(); // Rules:
                // - default = array
                // - when using 2 block params = object
                // - when using @key = object

                if (childScope.iterationType === _Context.IterationType.ARRAY) {
                  // Array iteration
                  _this.buffer.push("{% for " + childScope.value + " in " + _condition + " %}");
                } else {
                  // Object iteration
                  var key = 'key';
                  var value = 'value';

                  if (childScope.value) {
                    value = childScope.value;
                    key = childScope.key || 'key';
                  }

                  _this.buffer.push("{% for " + key + ", " + value + " in " + _condition + ".items %}");
                }

                _this.buffer.push(_t2.toString());

                _this.buffer.push("{% endfor %}");

                break;
              }

            default:
              {
                // tslint:disable-next-line:no-console
                console.log('Unsupported block ', type);

                _this.buffer.push("{{# " + type + " }}");

                var _t3 = new DjangoTranspiler(null, _this.context, _this.depth);

                _t3.parseProgram(statement.program);

                _this.buffer.push(_t3.toString());

                _this.buffer.push("{{/" + type + "}}");
              }
          }

          break;

        case 'PartialStatement':
          {
            var name;

            if (statement.name.type === 'StringLiteral') {
              var expression = statement.name;
              name = "\"" + expression.value.replace('.hbs', '.html') + "\"";
            } else if (statement.name.type === 'SubExpression') {
              var _expression = statement.name; // TODO: add generic helper support, which includes lookup

              if (_expression.path.original === 'lookup') {
                // TODO: add scope support, now always assumes '.' (current scope)
                name = _expression.params[1].value;
              }
            } else {
              name = statement.name.parts.filter(function (p) {
                return p !== 'hbs';
              }).join('/');
              name = "\"" + name + ".html\"";
            }

            var context = '';

            if (statement.params.length) {
              // TODO: django doesn't support pushing/replacing the context, only adding/replacing additional variables
              context = " with " + _this.context.getScopedVariable(statement.params[0]) + "=\"does-not-work\"";
            }

            var params = '';

            if (statement.hash) {
              params = ' with ' + statement.hash.pairs.map(function (pair) {
                var key = pair.key + "=";

                if (pair.value.type === 'PathExpression') {
                  return "" + key + _this.context.getScopedVariable(pair.value);
                }

                if (pair.value.type === 'StringLiteral') {
                  return key + "\"" + pair.value.value + "\"";
                }

                if (pair.value.type === 'NumberLiteral') {
                  return "" + key + pair.value.value;
                }

                if (pair.value.type === 'BooleanLiteral') {
                  return "" + key + pair.value.value;
                }

                return '';
              }).filter(function (_) {
                return _;
              }).join(' ');
            }

            _this.buffer.push("{% include " + name + context + params + " %}");

            break;
          }

        default:
          {
            // tslint:disable-next-line:no-console
            console.log('Unsupported statements ', statement.type);
          }
      }
    });
    return this;
  };
  /**
   * Checks if this sub-program has only a condition statement.
   * If that's the case, and used in a inverse (else) section, the parent should render `else if`
   * instead of an `if` nested in an `else`.
   * @param {hbs.AST.Program} program
   * @return {boolean}
   */


  DjangoTranspiler.isOnlyCondition = function isOnlyCondition(program) {
    return program.body.length === 1 && program.body[0].type === 'BlockStatement' && program.body[0].path.original === 'if';
  };

  _proto.toString = function toString() {
    return this.buffer.reduce(function (str, op) {
      return str + op;
    }, '');
  };

  return DjangoTranspiler;
}();

exports.DjangoTranspiler = DjangoTranspiler;
