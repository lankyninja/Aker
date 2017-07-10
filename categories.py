#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy 
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'


import logging, re, json


class CategoryRuleEngine(object):
    """
    This class is resposnible for loading and returning rules based on a configuration
    """
    RuleEngineInstance=None

    def __init__(self,configuration=None):
        logging.debug("LOADING CategoryRuleEngine")
        self.RuleList = {}
        self.Categories = []
        self._initialise_engine(configuration)
        CategoryRuleEngine.RuleEngineInstance = self

    def _initialise_engine(self,configuration=None):
        self.addRule(RegexRule())
        self.addRule(BasicRule())

        if configuration is not None:
            if configuration.get("categories_allow_cidr") is True:
                self.addRule(CidrRule())
            logging.debug("Configuration is not null")
            config_path=configuration.get("categories_path")
            categories = json.load(open(config_path,'r'))
            for category in categories:
                listOfRules = []
                for rule in categories[category]: 
                    listOfRules.append(CategoryRules(rule_type=rule.get("type"),target=rule.get("target"),rules=rule.get("rules")))
                self.Categories.append(Category(category,listOfRules))


    def _getRule(self,rule_type):
        """
        Returns a rule based on type (regex, basic, CIDR)
        """

        if type(rule_type) != str:
            raise Exception("Rule type must be a string ")

        if rule_type not in self.RuleList.keys():
            return None

        return self.RuleList.get(rule_type)
        
    @staticmethod
    def getRule(rule_type):
        return CategoryRuleEngine.getRuleEngine()._getRule(rule_type)


    def addRule(self,rule_instance):
        self.RuleList.update(dict().fromkeys((rule_instance.getName(),),rule_instance))

    @staticmethod
    def getRuleEngine():
        if CategoryRuleEngine.RuleEngineInstance is None:
            CategoryRuleEngine.RuleEngineInstance = CategoryRuleEngine()

        return CategoryRuleEngine.RuleEngineInstance

    def _getCategories(self):
        return self.Categories

    @staticmethod
    def getCategories():
        return CategoryRuleEngine.getRuleEngine()._getCategories()


class Rule(object):
    """
    Base class to implement shared functionality
    This should enable different rules to be impletemented when building categories
    """
    def __init__(self,rule_name):
        self.name=rule_name
        logging.debug("Loading the %s rule",self.getName())


    def hostMatches(self,host,rule):
        """
        Checks if the target field on a host object matches a rule 
        returns: Boolean
        """
        logging.info("%s has not implemented `hostMatches()` yet",self.getName())


    def getName(self):
        """
        Returns the name of the rule type
        """
        return self.name
        



class RegexRule(Rule):
    """
    Matches the target parameter based on a regular expression
    """
    def __init__(self):
        super(RegexRule,self).__init__("REGEX")

    def hostMatches(self,host,rule):
        target = getattr(host,rule.target,None)    
        rules = rule.rule_values


        logging.debug("Rule target is %s, Target is: %s, Host is: %s",rule.target,target,type(host))
        if target is None:
            return False

        for rule in rules:
            logging.debug("REGEX: Matching %s against %s",target,str(rule))
            re.compile(str(rule))
            if re.match(target) is not None:
                return True

        return False


class BasicRule(Rule):
    """
    Matches the target parameter on an exact match: ==
    """
    def __init__(self):
        super(BasicRule,self).__init__("BASIC")



class CidrRule(Rule):
    """
    Matches the target parameter based on a CIDR validation.  Must be enabled in configuration
    """
    def __init__(self):
        super(CidrRule,self).__init__("CIDR")



class Category(object):
    """
    This hold basic mappings for category objects
    """
    def __init__(self,name,rules = []):
        self.name = str(name)
        self.rules = rules

class CategoryRules(object):
    def __init__(self,rule_type,target,rules):
        self.type = str(rule_type)
        self.target = str(target)
        self.rule_values = rules