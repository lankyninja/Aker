# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy 
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import json
import logging
import redis
from IdPFactory import IdPFactory




class Host(object):
	"""
	Class representing a single server entry , servers have the following attributes :
	
	name: FQDN of server
	ssh_port: server ssh port , default is 22
	categories: list of categories that the host belongs to
	"""
	
	def __init__(self, name,description="", ssh_port=22, private_key_path="",categories = []):
		self.fqdn = str(name)
		self.description=str(description)
		self.ssh_port = int(ssh_port)
		self.categories = categories
		self.key_path = str(private_key_path)
   
	def equal(self,server):
		if self.fqdn == server.fqdn and self.ssh_port == server.ssh_port:
			return True
		else:
			return False
            
	def __str__(self):
		return "fqdn:%s, ssh_port:%d" % (self.fqdn, self.ssh_port)
		
	def __iter__(self):
		return self

	def addCategory(self,category):
		if category not in self.categories:
			self.categories.append(category)


class Hosts(object):
	"""
	A class to handle all interactions with hosts allowed to the user,
	it handles operations between cache(Redis) and backend identity providers
	like IPA, Json etc..
	
	The responsibility of defining HBAC (hosts allowed to the user) lies on the
	underlaying identity provider .
	"""
	def __init__(self,config,username,gateway_hostgroup,idp,rule_engine):
		# This will handle the association and matching of categories
		self.categories_engine = rule_engine
		self._allowed_ssh_hosts = []
		self.user = username
		# username is the redis key, well kinda 
		self.user_cache_key = self.user+":hosts"
		self.gateway_hostgroup = gateway_hostgroup
		self.idp = IdPFactory.getIdP(idp)(config,username,gateway_hostgroup)
		#TODO: do we need a configurable redis host?
		self.redis = self._init_redis_conn('localhost')
		
		
	def _init_redis_conn(self,RedisHost):
		redis_connection = redis.StrictRedis(RedisHost, db=0, decode_responses = True)		
		try:
			if redis_connection.ping():
				return redis_connection
		except Exception as e:
			logging.error("Hosts: all subsequent calls will fallback to backened idp, cache error: {0}".format(e.message))
			return None
	
	def _load_hosts_from_cache(self, hkey):
		
		result = self.redis.hgetall(hkey)
		cached = False
		if result is not None:
			try:
				#Clear our list first
				del self._allowed_ssh_hosts[:]
				
				for k,v in result.iteritems():
					self._allowed_ssh_hosts.append(json.loads(v))
					cached = True
			except Exception as e:
				logging.error("Hosts: redis error: {0}".format(e.message))
				cached = False 			
		else:
			logging.info("Hosts: no hosts loaded from cache for user %s" % self.user) 
			cached = False
				
		return cached 

	
	def _save_hosts_to_cache(self, hosts):
		"""
		hosts passed to this function should be a list of Host object		
		"""
		# Delete existing cache if any
		self._del_cache_key(self.user_cache_key)
		logging.debug("Hosts: deleting hosts for user {0} from cache".format(self.user))
		
		for host in hosts:
			try:
				# Save to redis under $user:hosts
				self.redis.hset(self.user_cache_key,host.fqdn,json.dumps(vars(host)))
				logging.debug("Hosts: adding host {0} to cache".format(host))
				host = None
			except Exception as e:
				logging.error("Hosts: error saving to cache : {0}".format(e.message))
		
		
	
	def _del_cache_key(self,hkey):
		try:
			self.redis.delete(hkey)
		except Exception as e:
			logging.error("Hosts: error deleting from cache : {0}".format(e.message))
			
	
	def list_allowed(self,from_cache=True):
		
		cached=False
		
		#load from cache
		if from_cache:
			# is redis up ?
			if self.redis is not None :
				cached = self._load_hosts_from_cache(self.user_cache_key)
		
		#backened cache has some entries for us
		if cached is True :
			logging.info("Hosts: loading hosts from cache")
			return self._allowed_ssh_hosts
		else:
			del self._allowed_ssh_hosts[:]

			self._allowed_ssh_hosts = self.idp.list_allowed()

			for host in self._allowed_ssh_hosts:
				for category in self.categories_engine.getCategories():
					for rule in category.rules:
						Rule = self.categories_engine.getRule(rule.type)
						if Rule is not None and Rule.hostMatches(host=host,rule=rule):
							logging.debug("Host matches rule")
							host.addCategory(category)
							break

			if self.redis is not None :
				self._save_hosts_to_cache(self._allowed_ssh_hosts)
			return self._allowed_ssh_hosts























