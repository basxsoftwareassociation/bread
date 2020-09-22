"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");

exports.__esModule = true;
exports.IterationType = exports.Scope = exports.default = void 0;

var _extends2 = _interopRequireDefault(require("@babel/runtime/helpers/extends"));

/**
 * Holds information about the current Handlebars Context.
 * A new context is created when traversing inside a block that introduces new variables, e.g. 'each'
 *
 * Creating a child context is done by calling context.createChildContext([variables in scope]).
 * This will clone the current context, append the new scope, and increase the depth
 */
var Context =
/*#__PURE__*/
function () {
  /**
   * A list of scopes, length should correspond with `depth-1`
   */

  /**
   * Context depth, will be increased when creating a child context
   */

  /**
   * object will be shared between parent and child contexts
   */
  function Context() {
    Object.defineProperty(this, "scopes", {
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
    Object.defineProperty(this, "shared", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    // create empty scope at root level
    this.scopes = [new Scope([])]; // set initial depth to 0

    this.depth = 0;
    this.shared = {
      ifCounter: 0
    };
  }
  /**
   * Add new values to the context and return the new context. The current context remains untouched.
   * @param {string[]} variables
   * @param replacements
   * @return {Context} A new context.
   */


  var _proto = Context.prototype;

  _proto.createChildContext = function createChildContext(variables, replacements) {
    var context = this.clone();
    context.scopes.push(new Scope(variables, replacements));
    ++context.depth;
    return context;
  };
  /**
   * Gets the scope for a given depth
   *
   * @param {number} depth
   * @return {Scope}
   */


  _proto.getScope = function getScope(depth) {
    return this.scopes[depth];
  };

  _proto.getCurrentScope = function getCurrentScope() {
    return this.scopes[this.scopes.length - 1];
  };
  /**
   * Gets all the available variables available in the scopes up to the given depth.
   * Can be used to see if a variable is explicitly referencing a scope variable
   * @param {number} depth
   * @return {Array<string>}
   */


  _proto.getScopesToDepth = function getScopesToDepth(depth) {
    // NOTE: contains duplicates, but doesn't matter
    var mergedScope = {
      variables: [],
      replacements: []
    };
    this.scopes.slice(0, depth + 1).forEach(function (scope) {
      if (scope.variables) {
        var _mergedScope$variable;

        (_mergedScope$variable = mergedScope.variables).push.apply(_mergedScope$variable, scope.variables);
      }

      if (scope.replacements) {
        mergedScope.replacements = (0, _extends2.default)({}, mergedScope.replacements, scope.replacements);
      }
    });
    return mergedScope;
  };

  _proto.getScopedVariable = function getScopedVariable(path) {
    // get the depth the variable is referencing (path.depth is higher when using ../)
    var varDepth = this.depth - path.depth; // console.log('getScopedVariable', path);

    if (varDepth === 0) {
      // upper level is root, which has no scope vars, so do early exit
      return path.parts.join('.');
    } // if the variable doesn't match anything explicitly, and is not in the root scope,
    // we must prepend it with the current scope value (at least for 'each' blocks)


    var currentScope = this.getScope(varDepth); // {{ this }}

    if (path.parts.length === 0) {
      return currentScope.value;
    } // {{ @key }}


    if (path.original === '@key') {
      // when no key is provided by `|value key|`, it will be added in the output template by default
      if (!currentScope.key) {
        currentScope.iterateAsObject();
      }

      return currentScope.key || 'key';
    } // get the scope by traversing up to a certain parent depth
    // when using ../ in the variable, the depth will lower
    // this will build op all explicit scope variables from the root up to the provided depth


    var _getScopesToDepth = this.getScopesToDepth(varDepth),
        variables = _getScopesToDepth.variables,
        replacements = _getScopesToDepth.replacements; // if the first path of the variable already in the current scope, or any parents


    if (variables.includes(path.parts[0])) {
      var match = path.parts.join('.');

      if (match in replacements) {
        return replacements[match];
      }

      return match;
    } // console.log(' >> ', currentScope.value, path.parts);

    if(!currentScope)
      return '???';

    return [currentScope.value, path.parts.join('.')].join('.');
  }; // clone the current Context


  _proto.clone = function clone() {
    var context = new Context();
    context.scopes = this.scopes.concat();
    context.depth = this.depth;
    context.shared = this.shared;
    return context;
  };

  return Context;
}();
/**
 * Internal scope class, created when increasing the context depth.
 * Contains all the variables in the new scope.
 */


exports.default = Context;

var Scope =
/*#__PURE__*/
function () {
  // alias vars for easy reference, these ones are for the `each` loop
  function Scope(variables, replacements) {
    Object.defineProperty(this, "iterationType", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: IterationType.ARRAY
    });
    Object.defineProperty(this, "variables", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    Object.defineProperty(this, "replacements", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    Object.defineProperty(this, "value", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    Object.defineProperty(this, "key", {
      configurable: true,
      enumerable: true,
      writable: true,
      value: void 0
    });
    this.variables = variables;
    this.replacements = replacements; // NOTE: might require additional info if we handle other type of blockParam variables

    this.value = this.variables[0];
    this.key = this.variables[1] || undefined;
  }

  var _proto2 = Scope.prototype;

  _proto2.iterateAsObject = function iterateAsObject() {
    this.iterationType = IterationType.OBJECT;
  };

  return Scope;
}();

exports.Scope = Scope;
var IterationType;
exports.IterationType = IterationType;

(function (IterationType) {
  IterationType[IterationType["ARRAY"] = 'array'] = "ARRAY";
  IterationType[IterationType["OBJECT"] = 'object'] = "OBJECT";
})(IterationType || (exports.IterationType = IterationType = {}));
